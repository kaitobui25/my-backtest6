"""
Generate a small deterministic 15-minute OHLCV Parquet file for smoke tests.

This is not market data and must not be used to judge strategy profitability.
It only proves installation, loading, batching, checkpoints, and output files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    rng = np.random.default_rng(7)
    timestamps = pd.date_range("2021-01-01", periods=96 * 120, freq="15min", tz="UTC")
    returns = rng.normal(0.0, 0.0015, len(timestamps))
    close = 30_000.0 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.maximum(close * rng.uniform(0.0002, 0.002, len(close)), 1.0)
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.lognormal(3.0, 0.5, len(close))

    frame = pd.DataFrame(
        {
            "datetime": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )
    output = Path(__file__).resolve().parents[1] / "data" / "btcusdt_15m.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    print(output)


if __name__ == "__main__":
    main()
