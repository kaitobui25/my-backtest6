"""
Parquet OHLCV loading, normalization, validation, and split selection.

Timestamp auto-detection accepts common candle-open column names and timestamps
stored in a Parquet index. Column names are matched case-insensitively after
normalizing spaces and punctuation. Numeric Unix timestamps are inferred as
seconds, milliseconds, microseconds, or nanoseconds and converted to UTC.

Previous-day high/low are calculated on full history before a split is sliced,
so the first tested day can use the previous completed UTC day without
lookahead.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .types import CandleData

_TIMESTAMP_ALIASES = (
    "datetime",
    "date",
    "timestamp",
    "time",
    "open_time",
    "open_timestamp",
    "start_time",
    "candle_open_time",
)
_REQUIRED_NUMERIC = ("open", "high", "low", "close", "volume")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_name(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def _schema_description(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    return (
        f"columns={columns}; "
        f"index={type(frame.index).__name__}(name={frame.index.name!r})"
    )


def _matching_column(frame: pd.DataFrame, normalized_name: str) -> Any | None:
    matches = [
        column
        for column in frame.columns
        if _normalize_name(column) == normalized_name
    ]
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous columns for '{normalized_name}': "
            f"{[str(column) for column in matches]}"
        )
    return None if not matches else matches[0]


def _infer_epoch_unit(values: pd.Series) -> str | None:
    numeric = pd.to_numeric(values, errors="coerce")
    finite = numeric[
        np.isfinite(numeric.to_numpy(dtype=np.float64, na_value=np.nan))
    ]
    if finite.empty:
        return None

    magnitude = float(finite.abs().median())
    if magnitude >= 1e17:
        return "ns"
    if magnitude >= 1e14:
        return "us"
    if magnitude >= 1e11:
        return "ms"
    if magnitude >= 1e8:
        return "s"
    return None


def _parse_timestamp(values: pd.Series) -> pd.Series:
    if isinstance(values.dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_dtype(
        values.dtype
    ):
        return pd.to_datetime(values, utc=True, errors="coerce")

    numeric = pd.to_numeric(values, errors="coerce")
    non_null = values.notna()
    numeric_ratio = (
        float(numeric[non_null].notna().mean()) if bool(non_null.any()) else 0.0
    )
    if numeric_ratio >= 0.95:
        unit = _infer_epoch_unit(numeric)
        if unit is not None:
            return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")

        finite = numeric.dropna()
        if not finite.empty:
            integer_values = finite.round().astype("int64")
            if integer_values.between(19_000_101, 22_001_231).all():
                compact = numeric.round().astype("Int64").astype("string")
                return pd.to_datetime(
                    compact,
                    format="%Y%m%d",
                    utc=True,
                    errors="coerce",
                )

    return pd.to_datetime(values, utc=True, errors="coerce")


def _index_looks_like_timestamp(index: pd.Index) -> bool:
    if isinstance(index, pd.DatetimeIndex):
        return True
    if isinstance(index, pd.RangeIndex) or len(index) == 0:
        return False

    sample = pd.Series(index[: min(len(index), 256)])
    parsed = _parse_timestamp(sample)
    if parsed.notna().mean() < 0.95:
        return False

    years = parsed.dropna().dt.year
    return not years.empty and years.between(1990, 2200).all()


def _materialize_timestamp_index(
    frame: pd.DataFrame,
    configured: str | None,
) -> pd.DataFrame:
    if isinstance(frame.index, pd.MultiIndex):
        return frame

    configured_normalized = _normalize_name(configured) if configured else "auto"
    index_name_normalized = (
        _normalize_name(frame.index.name) if frame.index.name is not None else ""
    )
    column_has_timestamp = any(
        _matching_column(frame, alias) is not None for alias in _TIMESTAMP_ALIASES
    )

    if configured_normalized not in ("auto", "index"):
        configured_column = _matching_column(frame, configured_normalized)
        if configured_column is not None:
            return frame

    use_index = configured_normalized == "index"
    use_index |= not column_has_timestamp and isinstance(
        frame.index,
        pd.DatetimeIndex,
    )
    use_index |= (
        not column_has_timestamp
        and bool(index_name_normalized)
        and index_name_normalized in _TIMESTAMP_ALIASES
    )
    use_index |= (
        configured_normalized not in ("auto", "index")
        and index_name_normalized == configured_normalized
    )
    use_index |= not column_has_timestamp and _index_looks_like_timestamp(frame.index)

    if not use_index:
        return frame

    column_name = str(frame.index.name) if frame.index.name is not None else "datetime"
    if column_name in frame.columns:
        column_name = "__timestamp_index__"

    result = frame.reset_index(drop=True)
    result.insert(0, column_name, frame.index.to_numpy(copy=False))
    return result


def _canonicalize_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rename: dict[Any, str] = {}
    for canonical in _REQUIRED_NUMERIC:
        if canonical in frame.columns:
            continue
        match = _matching_column(frame, canonical)
        if match is not None:
            rename[match] = canonical
    return frame.rename(columns=rename) if rename else frame


def _find_timestamp_column(frame: pd.DataFrame, configured: str | None) -> Any:
    if configured and configured != "auto":
        configured_normalized = _normalize_name(configured)
        if configured_normalized == "index":
            configured_normalized = "datetime"
        match = _matching_column(frame, configured_normalized)
        if match is None:
            raise ValueError(
                f"Configured timestamp column not found: {configured!r}. "
                f"{_schema_description(frame)}"
            )
        return match

    for candidate in _TIMESTAMP_ALIASES:
        match = _matching_column(frame, candidate)
        if match is not None:
            return match

    raise ValueError(
        "Missing timestamp column. Accepted normalized names: "
        f"{_TIMESTAMP_ALIASES}. {_schema_description(frame)}"
    )


def load_parquet(path: str | Path, timestamp_column: str | None = "auto") -> CandleData:
    data_path = Path(path).resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Parquet data not found: {data_path}")

    frame = pd.read_parquet(data_path)
    frame = _materialize_timestamp_index(frame, timestamp_column)
    frame = _canonicalize_numeric_columns(frame)
    timestamp_name = _find_timestamp_column(frame, timestamp_column)

    missing = set(_REQUIRED_NUMERIC) - set(frame.columns)
    if missing:
        raise ValueError(
            f"Data is missing columns: {sorted(missing)}. "
            f"{_schema_description(frame)}"
        )

    frame = frame.rename(columns={timestamp_name: "datetime"}).copy()
    frame["datetime"] = _parse_timestamp(frame["datetime"])
    for column in _REQUIRED_NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    bad_null = frame[["datetime", *_REQUIRED_NUMERIC]].isna().any(axis=1)
    if bad_null.any():
        raise ValueError(
            "Data contains invalid timestamp/OHLCV rows:\n"
            + frame.loc[bad_null, ["datetime", *_REQUIRED_NUMERIC]]
            .head(10)
            .to_string(index=False)
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
            + frame.loc[invalid_ohlc, ["datetime", *_REQUIRED_NUMERIC]]
            .head(10)
            .to_string(index=False)
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
    day_id = (
        frame["trading_day"].astype("int64") // 86_400_000_000_000
    ).to_numpy(np.int64)

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
