"""
PDH/PDL Liquidity Sweep + Reclaim strategy plugin.

Strategy-only responsibilities:
- track long/short sweep setup state while the execution engine is flat;
- reject candles sweeping both previous-day levels;
- allow same-candle sweep + reclaim;
- expire a setup after max_wait_candles, counting the sweep candle;
- return direction, stop specification, and setup start index.

It does NOT implement entry timing, SL/TP fills, fees, slippage, both-hit order,
position overlap, max-hold, end-of-data close, metrics, or trade records. Those
rules exist once in execution/kernel_factory.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import njit

from exactbt.constants import STOP_ABSOLUTE_PRICE
from exactbt.optimization.grid import expand_parameter_grid
from exactbt.types import CandleData, EncodedStrategyParameters, StrategyFeatures

# Integer state layout.
_PREVIOUS_DAY = 0
_LONG_ACTIVE = 1
_LONG_START = 2
_SHORT_ACTIVE = 3
_SHORT_START = 4

# Float state layout.
_LONG_EXTREME = 0
_SHORT_EXTREME = 1

# Float parameter layout.
_SWEEP_BUFFER = 0
_RECLAIM_BUFFER = 1
_STOP_BUFFER = 2

# Integer parameter layout.
_MAX_WAIT = 0


@njit(cache=True)
def reset_state_nb(state_i: np.ndarray, state_f: np.ndarray) -> None:
    state_i[_PREVIOUS_DAY] = -1
    state_i[_LONG_ACTIVE] = 0
    state_i[_LONG_START] = -1
    state_i[_SHORT_ACTIVE] = 0
    state_i[_SHORT_START] = -1
    state_f[_LONG_EXTREME] = np.nan
    state_f[_SHORT_EXTREME] = np.nan


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
    """Advance setup state by one eligible candle and optionally emit a signal."""
    current_day = day_id[i]
    if state_i[_PREVIOUS_DAY] != current_day:
        state_i[_PREVIOUS_DAY] = current_day
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_LONG_EXTREME] = np.nan
        state_f[_SHORT_EXTREME] = np.nan

    pdh = feature_f[0, i]
    pdl = feature_f[1, i]
    if np.isnan(pdh) or np.isnan(pdl):
        return 0, np.nan, STOP_ABSOLUTE_PRICE, -1

    max_wait = params_i[_MAX_WAIT]
    if state_i[_LONG_ACTIVE] == 1 and i - state_i[_LONG_START] >= max_wait:
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_f[_LONG_EXTREME] = np.nan
    if state_i[_SHORT_ACTIVE] == 1 and i - state_i[_SHORT_START] >= max_wait:
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_SHORT_EXTREME] = np.nan

    sweep_buffer = params_f[_SWEEP_BUFFER]
    reclaim_buffer = params_f[_RECLAIM_BUFFER]
    stop_buffer = params_f[_STOP_BUFFER]

    sweep_long = low[i] < pdl * (1.0 - sweep_buffer)
    sweep_short = high[i] > pdh * (1.0 + sweep_buffer)

    if sweep_long and sweep_short:
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_LONG_EXTREME] = np.nan
        state_f[_SHORT_EXTREME] = np.nan
        return 0, np.nan, STOP_ABSOLUTE_PRICE, -1

    if sweep_long and state_i[_LONG_ACTIVE] == 0:
        state_i[_LONG_ACTIVE] = 1
        state_i[_LONG_START] = i
        state_f[_LONG_EXTREME] = low[i]

    if sweep_short and state_i[_SHORT_ACTIVE] == 0:
        state_i[_SHORT_ACTIVE] = 1
        state_i[_SHORT_START] = i
        state_f[_SHORT_EXTREME] = high[i]

    if state_i[_LONG_ACTIVE] == 1:
        state_f[_LONG_EXTREME] = min(state_f[_LONG_EXTREME], low[i])
    if state_i[_SHORT_ACTIVE] == 1:
        state_f[_SHORT_EXTREME] = max(state_f[_SHORT_EXTREME], high[i])

    long_reclaimed = (
        state_i[_LONG_ACTIVE] == 1
        and close[i] >= pdl * (1.0 + reclaim_buffer)
    )
    short_reclaimed = (
        state_i[_SHORT_ACTIVE] == 1
        and close[i] <= pdh * (1.0 - reclaim_buffer)
    )

    if long_reclaimed and short_reclaimed:
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_LONG_EXTREME] = np.nan
        state_f[_SHORT_EXTREME] = np.nan
        return 0, np.nan, STOP_ABSOLUTE_PRICE, -1

    if long_reclaimed:
        setup_start = state_i[_LONG_START]
        stop_price = state_f[_LONG_EXTREME] * (1.0 - stop_buffer)
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_LONG_EXTREME] = np.nan
        state_f[_SHORT_EXTREME] = np.nan
        return 1, stop_price, STOP_ABSOLUTE_PRICE, setup_start

    if short_reclaimed:
        setup_start = state_i[_SHORT_START]
        stop_price = state_f[_SHORT_EXTREME] * (1.0 + stop_buffer)
        state_i[_LONG_ACTIVE] = 0
        state_i[_LONG_START] = -1
        state_i[_SHORT_ACTIVE] = 0
        state_i[_SHORT_START] = -1
        state_f[_LONG_EXTREME] = np.nan
        state_f[_SHORT_EXTREME] = np.nan
        return -1, stop_price, STOP_ABSOLUTE_PRICE, setup_start

    return 0, np.nan, STOP_ABSOLUTE_PRICE, -1


@dataclass(frozen=True)
class LiquiditySweepPlugin:
    name: str = "liquidity_sweep_reclaim"
    version: str = "1"
    state_float_size: int = 2
    state_int_size: int = 5
    step_nb: Any = step_nb
    reset_state_nb: Any = reset_state_nb

    def expand_grid(self, parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
        return expand_parameter_grid(parameter_spec)

    def prepare_features(
        self,
        candles: CandleData,
        configs: list[dict[str, Any]],
    ) -> StrategyFeatures:
        del configs
        feature_f = np.ascontiguousarray(
            np.vstack([
                candles.frame["pdh"].to_numpy(np.float64),
                candles.frame["pdl"].to_numpy(np.float64),
            ])
        )
        return StrategyFeatures(
            float_features=feature_f,
            int_features=np.empty((0, len(candles.open)), dtype=np.int64),
            metadata={"float_rows": {"pdh": 0, "pdl": 1}},
        )

    def encode_parameters(
        self,
        configs: list[dict[str, Any]],
        features: StrategyFeatures,
    ) -> EncodedStrategyParameters:
        del features
        float_params = np.empty((len(configs), 3), dtype=np.float64)
        int_params = np.empty((len(configs), 1), dtype=np.int64)
        for row, config in enumerate(configs):
            float_params[row] = (
                float(config["sweep_buffer_ratio"]),
                float(config["reclaim_buffer_ratio"]),
                float(config["stop_buffer_ratio"]),
            )
            int_params[row, 0] = int(config["max_wait_candles"])
        return EncodedStrategyParameters(
            float_params=np.ascontiguousarray(float_params),
            int_params=np.ascontiguousarray(int_params),
        )


PLUGIN = LiquiditySweepPlugin()
