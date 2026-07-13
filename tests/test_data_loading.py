"""Parquet schema compatibility tests for ExactBT data loading."""

from __future__ import annotations

import pandas as pd

from exactbt.data import load_parquet


def _ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10.0, 11.0],
        }
    )


def test_load_parquet_accepts_open_time_epoch_milliseconds(tmp_path):
    timestamps = pd.date_range("2023-01-01", periods=2, freq="5min", tz="UTC")
    frame = _ohlcv_frame().rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    frame.insert(
        0,
        "Open time",
        [timestamp.value // 1_000_000 for timestamp in timestamps],
    )
    path = tmp_path / "open_time_ms.parquet"
    frame.to_parquet(path, index=False)

    candles = load_parquet(path)

    assert candles.frame["datetime"].tolist() == timestamps.tolist()
    assert candles.open.tolist() == [100.0, 101.0]
    assert candles.volume.tolist() == [10.0, 11.0]


def test_load_parquet_accepts_unnamed_datetime_index(tmp_path):
    timestamps = pd.date_range("2023-01-01", periods=2, freq="15min", tz="UTC")
    frame = _ohlcv_frame()
    frame.index = timestamps
    frame.index.name = None
    path = tmp_path / "datetime_index.parquet"
    frame.to_parquet(path)

    candles = load_parquet(path)

    assert candles.frame["datetime"].tolist() == timestamps.tolist()


def test_load_parquet_accepts_case_insensitive_date_column(tmp_path):
    timestamps = pd.date_range("2023-01-01", periods=2, freq="30min", tz="UTC")
    frame = _ohlcv_frame()
    frame.insert(0, "Date", timestamps)
    path = tmp_path / "capitalized_date.parquet"
    frame.to_parquet(path, index=False)

    candles = load_parquet(path)

    assert candles.frame["datetime"].tolist() == timestamps.tolist()
