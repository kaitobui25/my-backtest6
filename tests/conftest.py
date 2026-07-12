"""Shared synthetic candle and test-strategy helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from numba import njit

from exactbt.constants import STOP_DISTANCE
from exactbt.execution.kernel_factory import build_kernel
from exactbt.types import CandleData


@njit(cache=False)
def immediate_reset_nb(state_i: np.ndarray, state_f: np.ndarray) -> None:
    # No mutable setup state is needed.
    return


@njit(cache=False)
def immediate_step_nb(
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
    # feature_i[0, i] stores a test signal: -1, 0, or +1.
    side = feature_i[0, i]
    if side == 0:
        return 0, np.nan, STOP_DISTANCE, -1
    return side, params_f[0], STOP_DISTANCE, i


def make_candles(
    open_: list[float],
    high: list[float],
    low: list[float],
    close: list[float],
    day_ids: list[int] | None = None,
) -> CandleData:
    count = len(open_)
    timestamps = pd.date_range("2023-01-01", periods=count, freq="15min", tz="UTC")
    frame = pd.DataFrame(
        {
            "datetime": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(count),
            "trading_day": timestamps.floor("D"),
            "pdh": np.full(count, np.nan),
            "pdl": np.full(count, np.nan),
        }
    )
    ids = np.array(day_ids if day_ids is not None else [1] * count, dtype=np.int64)
    return CandleData(
        frame=frame,
        timestamps_ns=frame["datetime"].astype("int64").to_numpy(np.int64),
        open=np.ascontiguousarray(np.array(open_, dtype=np.float64)),
        high=np.ascontiguousarray(np.array(high, dtype=np.float64)),
        low=np.ascontiguousarray(np.array(low, dtype=np.float64)),
        close=np.ascontiguousarray(np.array(close, dtype=np.float64)),
        volume=np.ones(count, dtype=np.float64),
        day_id=np.ascontiguousarray(ids),
    )


@pytest.fixture
def immediate_plugin_functions():
    return immediate_step_nb, immediate_reset_nb


@pytest.fixture(scope="session")
def immediate_kernel():
    return build_kernel(immediate_step_nb, immediate_reset_nb, 0, 0)
