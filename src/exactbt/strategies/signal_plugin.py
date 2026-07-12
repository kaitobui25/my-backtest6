"""
Generic adapter for stateless, close-confirmed long/short signal strategies.

Purpose:
- let many indicator strategies share one Numba `step_nb` implementation;
- precompute each unique signal combination only once;
- store signals compactly as int8 arrays;
- reuse ATR rows across all execution parameter combinations;
- keep entry, exits, fees, slippage, both-hit and records inside the one exact
  execution kernel rather than duplicating those rules in every strategy.

A concrete strategy module only needs a signal-builder function and one plugin
object. Execution parameters are normalized into every config so config IDs are
fully explicit and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd
from numba import njit

from exactbt.constants import STOP_DISTANCE
from exactbt.ids import stable_json
from exactbt.indicators import IndicatorCache
from exactbt.optimization.grid import expand_parameter_grid
from exactbt.types import CandleData, EncodedStrategyParameters, StrategyFeatures
from .signal_common import normalize_signals

SignalBuilder = Callable[[IndicatorCache, dict[str, Any]], tuple[pd.Series, pd.Series]]
ConfigValidator = Callable[[dict[str, Any]], bool]

# Parameters handled by the common execution adapter rather than signal logic.
_EXECUTION_KEYS = {
    "risk_reward",
    "max_hold_bars",
    "atr_stop_window",
    "atr_stop_multiplier",
    "side",
}

# Encoded parameter layouts.
_ATR_STOP_MULTIPLIER = 0
_LONG_SIGNAL_ROW = 0
_SHORT_SIGNAL_ROW = 1
_ATR_ROW = 2
_SIDE_MODE = 3  # 0 both, +1 long-only, -1 short-only


@njit(cache=True)
def reset_state_nb(state_i: np.ndarray, state_f: np.ndarray) -> None:
    """Stateless signal strategies do not carry setup state between candles."""
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
    """Read a precomputed close signal and return an ATR stop distance."""
    atr = feature_f[params_i[_ATR_ROW], i]
    if np.isnan(atr) or atr <= 0.0:
        return 0, np.nan, STOP_DISTANCE, -1

    long_hit = feature_i[params_i[_LONG_SIGNAL_ROW], i] != 0
    short_hit = feature_i[params_i[_SHORT_SIGNAL_ROW], i] != 0
    if long_hit and short_hit:
        return 0, np.nan, STOP_DISTANCE, -1

    side_mode = params_i[_SIDE_MODE]
    stop_distance = atr * params_f[_ATR_STOP_MULTIPLIER]
    if stop_distance <= 0.0 or np.isnan(stop_distance):
        return 0, np.nan, STOP_DISTANCE, -1

    if long_hit and side_mode >= 0:
        return 1, stop_distance, STOP_DISTANCE, i
    if short_hit and side_mode <= 0:
        return -1, stop_distance, STOP_DISTANCE, i
    return 0, np.nan, STOP_DISTANCE, -1


def _signal_parameters(config: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in config.items() if key not in _EXECUTION_KEYS}


def _normalized_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(config)
    normalized.setdefault("risk_reward", 2.0)
    normalized.setdefault("max_hold_bars", 0)
    normalized.setdefault("atr_stop_window", 14)
    normalized.setdefault("atr_stop_multiplier", 1.5)
    normalized.setdefault("side", "both")
    return normalized


@dataclass(frozen=True)
class PrecomputedSignalPlugin:
    """Plugin implementation shared by all simple indicator strategies."""

    name: str
    signal_builder: SignalBuilder
    version: str = "1"
    validator: ConfigValidator | None = None
    state_float_size: int = 0
    state_int_size: int = 0
    step_nb: Any = step_nb
    reset_state_nb: Any = reset_state_nb

    def expand_grid(self, parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
        configs = [_normalized_config(c) for c in expand_parameter_grid(parameter_spec)]
        if self.validator is not None:
            configs = [config for config in configs if self.validator(config)]
        for config in configs:
            if float(config["risk_reward"]) <= 0.0:
                raise ValueError(f"{self.name}: risk_reward must be > 0")
            if int(config["max_hold_bars"]) < 0:
                raise ValueError(f"{self.name}: max_hold_bars must be >= 0")
            if int(config["atr_stop_window"]) <= 1:
                raise ValueError(f"{self.name}: atr_stop_window must be > 1")
            if float(config["atr_stop_multiplier"]) <= 0.0:
                raise ValueError(f"{self.name}: atr_stop_multiplier must be > 0")
            if str(config["side"]) not in {"both", "long", "short"}:
                raise ValueError(f"{self.name}: side must be both, long, or short")
        return configs

    def prepare_features(
        self,
        candles: CandleData,
        configs: list[dict[str, Any]],
    ) -> StrategyFeatures:
        cache = IndicatorCache(candles)
        signal_rows: list[np.ndarray] = []
        signal_row_map: dict[str, tuple[int, int]] = {}

        # Deduplicate signal calculation across RR, stop multiplier, hold time,
        # ATR-stop window, and direction-only variants.
        for config in configs:
            signal_config = _signal_parameters(config)
            key = stable_json(signal_config)
            if key in signal_row_map:
                continue
            long_signal, short_signal = self.signal_builder(cache, signal_config)
            long_signal, short_signal = normalize_signals(long_signal, short_signal)
            long_row = len(signal_rows)
            signal_rows.append(long_signal.to_numpy(dtype=np.int8, copy=False))
            short_row = len(signal_rows)
            signal_rows.append(short_signal.to_numpy(dtype=np.int8, copy=False))
            signal_row_map[key] = (long_row, short_row)

        atr_rows: list[np.ndarray] = []
        atr_row_map: dict[int, int] = {}
        for window in sorted({int(config["atr_stop_window"]) for config in configs}):
            atr_row_map[window] = len(atr_rows)
            atr_rows.append(cache.atr(window).to_numpy(dtype=np.float64, copy=False))

        int_features = (
            np.ascontiguousarray(np.vstack(signal_rows), dtype=np.int8)
            if signal_rows
            else np.empty((0, len(candles.open)), dtype=np.int8)
        )
        float_features = (
            np.ascontiguousarray(np.vstack(atr_rows), dtype=np.float64)
            if atr_rows
            else np.empty((0, len(candles.open)), dtype=np.float64)
        )
        return StrategyFeatures(
            float_features=float_features,
            int_features=int_features,
            metadata={
                "signal_row_map": signal_row_map,
                "atr_row_map": atr_row_map,
            },
        )

    def encode_parameters(
        self,
        configs: list[dict[str, Any]],
        features: StrategyFeatures,
    ) -> EncodedStrategyParameters:
        signal_row_map = features.metadata["signal_row_map"]
        atr_row_map = features.metadata["atr_row_map"]
        side_codes = {"both": 0, "long": 1, "short": -1}

        float_params = np.empty((len(configs), 1), dtype=np.float64)
        int_params = np.empty((len(configs), 4), dtype=np.int64)
        for row, config in enumerate(configs):
            key = stable_json(_signal_parameters(config))
            long_row, short_row = signal_row_map[key]
            float_params[row, _ATR_STOP_MULTIPLIER] = float(config["atr_stop_multiplier"])
            int_params[row] = (
                long_row,
                short_row,
                atr_row_map[int(config["atr_stop_window"])],
                side_codes[str(config["side"])],
            )

        return EncodedStrategyParameters(
            float_params=np.ascontiguousarray(float_params),
            int_params=np.ascontiguousarray(int_params),
        )
