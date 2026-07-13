"""Rolling liquidity sweep + reclaim with an absolute wick-based stop.

Unlike the generic indicator adapter, this setup uses the swept candle's actual
extreme as the stop anchor. Levels are prior-bar rolling highs/lows, so the
signal has no lookahead. Entry, target, costs and fills remain in the one exact
execution kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import njit

from exactbt.constants import STOP_ABSOLUTE_PRICE
from exactbt.optimization.grid import expand_parameter_grid
from exactbt.types import CandleData, EncodedStrategyParameters, StrategyFeatures

_P_SWEEP_ATR = 0
_P_RECLAIM_ATR = 1
_P_STOP_ATR = 2

_P_UPPER_ROW = 0
_P_LOWER_ROW = 1
_P_ATR_ROW = 2
_P_REGIME_ROW = 3
_P_SIDE = 4
_P_USE_REGIME = 5


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
    upper = feature_f[params_i[_P_UPPER_ROW], i]
    lower = feature_f[params_i[_P_LOWER_ROW], i]
    atr = feature_f[params_i[_P_ATR_ROW], i]
    regime_ema = feature_f[params_i[_P_REGIME_ROW], i]
    if np.isnan(upper) or np.isnan(lower) or np.isnan(atr) or atr <= 0.0:
        return 0, np.nan, STOP_ABSOLUTE_PRICE, -1

    sweep_buffer = params_f[_P_SWEEP_ATR] * atr
    reclaim_buffer = params_f[_P_RECLAIM_ATR] * atr
    stop_buffer = params_f[_P_STOP_ATR] * atr
    side_mode = params_i[_P_SIDE]
    use_regime = params_i[_P_USE_REGIME] == 1

    long_regime_ok = (not use_regime) or (
        not np.isnan(regime_ema) and close[i] > regime_ema
    )
    short_regime_ok = (not use_regime) or (
        not np.isnan(regime_ema) and close[i] < regime_ema
    )

    long_hit = (
        side_mode >= 0
        and low[i] < lower - sweep_buffer
        and close[i] > lower + reclaim_buffer
        and close[i] > open_[i]
        and long_regime_ok
    )
    short_hit = (
        side_mode <= 0
        and high[i] > upper + sweep_buffer
        and close[i] < upper - reclaim_buffer
        and close[i] < open_[i]
        and short_regime_ok
    )

    if long_hit and short_hit:
        return 0, np.nan, STOP_ABSOLUTE_PRICE, -1
    if long_hit:
        return 1, low[i] - stop_buffer, STOP_ABSOLUTE_PRICE, i
    if short_hit:
        return -1, high[i] + stop_buffer, STOP_ABSOLUTE_PRICE, i
    return 0, np.nan, STOP_ABSOLUTE_PRICE, -1


@dataclass(frozen=True)
class RollingSweepReclaimPlugin:
    name: str = "rolling_sweep_reclaim"
    version: str = "1"
    state_float_size: int = 0
    state_int_size: int = 0
    step_nb: Any = step_nb
    reset_state_nb: Any = reset_state_nb

    def expand_grid(self, parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
        configs = expand_parameter_grid(parameter_spec)
        valid: list[dict[str, Any]] = []
        for config in configs:
            side = str(config.get("side", "both"))
            if side not in {"both", "long", "short"}:
                raise ValueError("rolling_sweep_reclaim: invalid side")
            for name in ("sweep_atr", "reclaim_atr", "stop_atr"):
                if float(config[name]) < 0.0:
                    raise ValueError(f"rolling_sweep_reclaim: {name} must be >= 0")
            if int(config["level_lookback"]) <= 1:
                raise ValueError("rolling_sweep_reclaim: level_lookback must be > 1")
            if int(config["atr_window"]) <= 1:
                raise ValueError("rolling_sweep_reclaim: atr_window must be > 1")
            if int(config.get("regime_ema", 0)) < 0:
                raise ValueError("rolling_sweep_reclaim: regime_ema must be >= 0")
            valid.append(config)
        return valid

    def prepare_features(
        self,
        candles: CandleData,
        configs: list[dict[str, Any]],
    ) -> StrategyFeatures:
        from exactbt.indicators import IndicatorCache

        cache = IndicatorCache(candles)
        rows: list[np.ndarray] = []
        row_map: dict[tuple[str, int], int] = {}

        for window in sorted({int(c["level_lookback"]) for c in configs}):
            row_map[("upper", window)] = len(rows)
            rows.append(cache.rolling_high(window).to_numpy(np.float64, copy=False))
            row_map[("lower", window)] = len(rows)
            rows.append(cache.rolling_low(window).to_numpy(np.float64, copy=False))

        for window in sorted({int(c["atr_window"]) for c in configs}):
            row_map[("atr", window)] = len(rows)
            rows.append(cache.atr(window).to_numpy(np.float64, copy=False))

        for window in sorted({int(c.get("regime_ema", 0)) for c in configs}):
            row_map[("regime", window)] = len(rows)
            if window > 0:
                rows.append(cache.ema(window).to_numpy(np.float64, copy=False))
            else:
                rows.append(np.full(len(candles.open), np.nan, dtype=np.float64))

        return StrategyFeatures(
            float_features=np.ascontiguousarray(np.vstack(rows)),
            int_features=np.empty((0, len(candles.open)), dtype=np.int8),
            metadata={"row_map": row_map},
        )

    def encode_parameters(
        self,
        configs: list[dict[str, Any]],
        features: StrategyFeatures,
    ) -> EncodedStrategyParameters:
        row_map = features.metadata["row_map"]
        side_codes = {"both": 0, "long": 1, "short": -1}
        float_params = np.empty((len(configs), 3), dtype=np.float64)
        int_params = np.empty((len(configs), 6), dtype=np.int64)
        for row, config in enumerate(configs):
            lookback = int(config["level_lookback"])
            atr_window = int(config["atr_window"])
            regime_window = int(config.get("regime_ema", 0))
            float_params[row] = (
                float(config["sweep_atr"]),
                float(config["reclaim_atr"]),
                float(config["stop_atr"]),
            )
            int_params[row] = (
                row_map[("upper", lookback)],
                row_map[("lower", lookback)],
                row_map[("atr", atr_window)],
                row_map[("regime", regime_window)],
                side_codes[str(config.get("side", "both"))],
                1 if regime_window > 0 else 0,
            )
        return EncodedStrategyParameters(
            float_params=np.ascontiguousarray(float_params),
            int_params=np.ascontiguousarray(int_params),
        )


PLUGIN = RollingSweepReclaimPlugin()
