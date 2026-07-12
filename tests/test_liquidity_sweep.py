"""Synthetic tests for the stateful PDH/PDL sweep-reclaim plugin."""

from __future__ import annotations

import numpy as np
import pandas as pd

from exactbt.execution.kernel_factory import build_kernel
from exactbt.execution.results import records_to_frame
from exactbt.strategies.liquidity_sweep import PLUGIN
from exactbt.types import CandleData


def test_same_candle_sweep_reclaim_enters_next_open():
    frame = pd.DataFrame(
        {
            "datetime": pd.date_range("2023-01-02", periods=3, freq="15min", tz="UTC"),
            "open": [101.0, 101.0, 101.0],
            "high": [102.0, 102.0, 105.0],
            "low": [99.0, 100.5, 100.0],
            "close": [100.5, 101.2, 105.0],
            "volume": [1.0, 1.0, 1.0],
            "pdh": [110.0, 110.0, 110.0],
            "pdl": [100.0, 100.0, 100.0],
        }
    )
    frame["trading_day"] = frame["datetime"].dt.floor("D")
    candles = CandleData(
        frame=frame,
        timestamps_ns=frame["datetime"].astype("int64").to_numpy(np.int64),
        open=np.array(frame["open"], dtype=np.float64),
        high=np.array(frame["high"], dtype=np.float64),
        low=np.array(frame["low"], dtype=np.float64),
        close=np.array(frame["close"], dtype=np.float64),
        volume=np.array(frame["volume"], dtype=np.float64),
        day_id=np.array([1, 1, 1], dtype=np.int64),
    )
    configs = [
        {
            "sweep_buffer_ratio": 0.0,
            "reclaim_buffer_ratio": 0.0,
            "stop_buffer_ratio": 0.0,
            "max_wait_candles": 4,
            "risk_reward": 2.0,
        }
    ]
    features = PLUGIN.prepare_features(candles, configs)
    encoded = PLUGIN.encode_parameters(configs, features)
    kernel = build_kernel(PLUGIN.step_nb, PLUGIN.reset_state_nb, 2, 5)
    _, record_i, record_f, count = kernel.one_with_records_nb(
        candles.open,
        candles.high,
        candles.low,
        candles.close,
        candles.volume,
        candles.day_id,
        features.float_features,
        features.int_features,
        encoded.float_params[0],
        encoded.int_params[0],
        2.0,
        0.0,
        0.0,
        0,
        True,
    )
    trades = records_to_frame(candles, record_i, record_f, count)
    assert len(trades) == 1
    assert trades.iloc[0]["setup_start_index"] == 0
    assert trades.iloc[0]["signal_index"] == 0
    assert trades.iloc[0]["entry_index"] == 1
    assert trades.iloc[0]["entry_price"] == 101.0
    assert trades.iloc[0]["stop_price"] == 99.0
    assert trades.iloc[0]["target_price"] == 105.0
