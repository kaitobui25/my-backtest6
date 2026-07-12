"""
Donchian Breakout + EMA Filter + ATR Stop example strategy plugin.

This second built-in family demonstrates that a strategy can be added without
copying the execution engine. Indicator arrays are cached once per unique
window across the full strategy grid, then each config stores only row indexes.
The Donchian channel is shifted one candle to prevent lookahead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from exactbt.constants import STOP_DISTANCE
from exactbt.optimization.grid import expand_parameter_grid
from exactbt.types import CandleData, EncodedStrategyParameters, StrategyFeatures

# Float parameters.
_ATR_MULTIPLIER = 0
# Integer parameters: feature-row indexes and side mode.
_EMA_ROW = 0
_ATR_ROW = 1
_UPPER_ROW = 2
_LOWER_ROW = 3
_SIDE_MODE = 4  # 0 both, 1 long only, -1 short only


@njit(cache=True)
def reset_state_nb(state_i: np.ndarray, state_f: np.ndarray) -> None:
    return


@njit(cache=True)
def step_nb(
    i: int,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
    day_id: np.ndarray,
    feature_f: np.ndarray,
    feature_i: np.ndarray,
    params_f: np.ndarray,
    params_i: np.ndarray,
    state_f: np.ndarray,
    state_i: np.ndarray,
) -> tuple[int, float, int, int]:
    ema = feature_f[params_i[_EMA_ROW], i]
    atr = feature_f[params_i[_ATR_ROW], i]
    upper = feature_f[params_i[_UPPER_ROW], i]
    lower = feature_f[params_i[_LOWER_ROW], i]
    if np.isnan(ema) or np.isnan(atr) or np.isnan(upper) or np.isnan(lower) or atr <= 0:
        return 0, np.nan, STOP_DISTANCE, -1

    side_mode = params_i[_SIDE_MODE]
    distance = atr * params_f[_ATR_MULTIPLIER]
    if side_mode >= 0 and close[i] > upper and close[i] > ema:
        return 1, distance, STOP_DISTANCE, i
    if side_mode <= 0 and close[i] < lower and close[i] < ema:
        return -1, distance, STOP_DISTANCE, i
    return 0, np.nan, STOP_DISTANCE, -1


def _wilder_atr(frame: pd.DataFrame, period: int) -> np.ndarray:
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean().to_numpy(np.float64)


@dataclass(frozen=True)
class DonchianEmaAtrPlugin:
    name: str = "donchian_ema_atr"
    version: str = "1"
    state_float_size: int = 0
    state_int_size: int = 0
    step_nb: Any = step_nb
    reset_state_nb: Any = reset_state_nb

    def expand_grid(self, parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
        return expand_parameter_grid(parameter_spec)

    def prepare_features(
        self,
        candles: CandleData,
        configs: list[dict[str, Any]],
    ) -> StrategyFeatures:
        frame = candles.frame
        rows: list[np.ndarray] = []
        row_map: dict[tuple[str, int], int] = {}

        for period in sorted({int(c["ema_window"]) for c in configs}):
            row_map[("ema", period)] = len(rows)
            rows.append(frame["close"].ewm(span=period, adjust=False, min_periods=period).mean().to_numpy(np.float64))

        for period in sorted({int(c["atr_window"]) for c in configs}):
            row_map[("atr", period)] = len(rows)
            rows.append(_wilder_atr(frame, period))

        for period in sorted({int(c["donchian_window"]) for c in configs}):
            row_map[("upper", period)] = len(rows)
            rows.append(frame["high"].rolling(period, min_periods=period).max().shift(1).to_numpy(np.float64))
            row_map[("lower", period)] = len(rows)
            rows.append(frame["low"].rolling(period, min_periods=period).min().shift(1).to_numpy(np.float64))

        return StrategyFeatures(
            float_features=np.ascontiguousarray(np.vstack(rows)),
            int_features=np.empty((0, len(candles.open)), dtype=np.int64),
            metadata={"row_map": row_map},
        )

    def encode_parameters(
        self,
        configs: list[dict[str, Any]],
        features: StrategyFeatures,
    ) -> EncodedStrategyParameters:
        row_map = features.metadata["row_map"]
        float_params = np.empty((len(configs), 1), dtype=np.float64)
        int_params = np.empty((len(configs), 5), dtype=np.int64)
        side_codes = {"both": 0, "long": 1, "short": -1}

        for row, config in enumerate(configs):
            float_params[row, _ATR_MULTIPLIER] = float(config["atr_stop_multiplier"])
            int_params[row] = (
                row_map[("ema", int(config["ema_window"]))],
                row_map[("atr", int(config["atr_window"]))],
                row_map[("upper", int(config["donchian_window"]))],
                row_map[("lower", int(config["donchian_window"]))],
                side_codes[str(config.get("side", "both"))],
            )

        return EncodedStrategyParameters(
            float_params=np.ascontiguousarray(float_params),
            int_params=np.ascontiguousarray(int_params),
        )


PLUGIN = DonchianEmaAtrPlugin()
