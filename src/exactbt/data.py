"""
Parquet OHLCV loading, normalization, validation, and split selection.

Accepted timestamp columns are `datetime`, `date`, `timestamp`, or `time`.
All timestamps are converted to UTC. Previous-day high/low are calculated on
full history before a split is sliced, so the first tested day can use the
previous completed UTC day without lookahead.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .types import CandleData

_TIMESTAMP_ALIASES = ("datetime", "date", "timestamp", "time")
_REQUIRED_NUMERIC = ("open", "high", "low", "close", "volume")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _find_timestamp_column(frame: pd.DataFrame, configured: str | None) -> str:
    if configured and configured != "auto":
        if configured not in frame.columns:
            raise ValueError(f"Configured timestamp column not found: {configured}")
        return configured
    for candidate in _TIMESTAMP_ALIASES:
        if candidate in frame.columns:
            return candidate
    raise ValueError(f"Missing timestamp column. Accepted: {_TIMESTAMP_ALIASES}")


def load_parquet(path: str | Path, timestamp_column: str | None = "auto") -> CandleData:
    data_path = Path(path).resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Parquet data not found: {data_path}")

    frame = pd.read_parquet(data_path)
    timestamp_name = _find_timestamp_column(frame, timestamp_column)

    missing = set(_REQUIRED_NUMERIC) - set(frame.columns)
    if missing:
        raise ValueError(f"Data is missing columns: {sorted(missing)}")

    frame = frame.rename(columns={timestamp_name: "datetime"}).copy()
    frame["datetime"] = pd.to_datetime(frame["datetime"], utc=True, errors="coerce")
    for column in _REQUIRED_NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    bad_null = frame[["datetime", *_REQUIRED_NUMERIC]].isna().any(axis=1)
    if bad_null.any():
        raise ValueError(
            "Data contains invalid timestamp/OHLCV rows:\n"
            + frame.loc[bad_null, ["datetime", *_REQUIRED_NUMERIC]].head(10).to_string(index=False)
        )

    frame = (
        frame.sort_values("datetime")
        .drop_duplicates("datetime", keep="last")
        .reset_index(drop=True)
    )

    invalid_ohlc = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
        | (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | (frame["volume"] < 0)
    )
    if invalid_ohlc.any():
        raise ValueError(
            "Data contains invalid OHLC rows:\n"
            + frame.loc[invalid_ohlc, ["datetime", *_REQUIRED_NUMERIC]].head(10).to_string(index=False)
        )

    frame["trading_day"] = frame["datetime"].dt.floor("D")
    daily = frame.groupby("trading_day", sort=True).agg(
        day_high=("high", "max"), day_low=("low", "min")
    )
    daily["pdh"] = daily["day_high"].shift(1)
    daily["pdl"] = daily["day_low"].shift(1)
    frame = frame.merge(
        daily[["pdh", "pdl"]],
        left_on="trading_day",
        right_index=True,
        how="left",
        validate="many_to_one",
    )

    # Integer UTC-day ID is cheap to compare inside Numba.
    day_id = (frame["trading_day"].astype("int64") // 86_400_000_000_000).to_numpy(np.int64)

    return CandleData(
        frame=frame,
        timestamps_ns=frame["datetime"].astype("int64").to_numpy(np.int64),
        open=np.ascontiguousarray(frame["open"].to_numpy(np.float64)),
        high=np.ascontiguousarray(frame["high"].to_numpy(np.float64)),
        low=np.ascontiguousarray(frame["low"].to_numpy(np.float64)),
        close=np.ascontiguousarray(frame["close"].to_numpy(np.float64)),
        volume=np.ascontiguousarray(frame["volume"].to_numpy(np.float64)),
        day_id=np.ascontiguousarray(day_id),
    )


def select_split(
    candles: CandleData,
    data_config: dict[str, Any],
    split_name: str,
    unlock_final_oos: bool,
) -> CandleData:
    splits = data_config.get("splits", {})
    if split_name not in splits:
        raise ValueError(f"Unknown split '{split_name}'. Available: {sorted(splits)}")

    split = splits[split_name]
    if bool(split.get("locked", False)) and not unlock_final_oos:
        raise PermissionError(
            f"Split '{split_name}' is locked. Use --unlock-final-oos only at the intended final milestone."
        )

    start = pd.Timestamp(split["start"])
    end = pd.Timestamp(split["end"])
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")

    mask = (candles.frame["datetime"] >= start) & (candles.frame["datetime"] < end)
    positions = np.flatnonzero(mask.to_numpy())
    if len(positions) == 0:
        raise ValueError(f"No candles in split {split_name}: {start} -> {end}")
    first, last = int(positions[0]), int(positions[-1]) + 1
    frame = candles.frame.iloc[first:last].reset_index(drop=True)

    return CandleData(
        frame=frame,
        timestamps_ns=np.ascontiguousarray(candles.timestamps_ns[first:last]),
        open=np.ascontiguousarray(candles.open[first:last]),
        high=np.ascontiguousarray(candles.high[first:last]),
        low=np.ascontiguousarray(candles.low[first:last]),
        close=np.ascontiguousarray(candles.close[first:last]),
        volume=np.ascontiguousarray(candles.volume[first:last]),
        day_id=np.ascontiguousarray(candles.day_id[first:last]),
    )
