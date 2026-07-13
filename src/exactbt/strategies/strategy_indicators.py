"""Additional cached indicators used by focused research strategies.

Kept separate from the original indicator library so v0.3 can be reviewed or
removed without changing existing strategy definitions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from exactbt.indicators import IndicatorCache


def adx(
    cache: IndicatorCache,
    window: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return Wilder ADX, +DI and -DI using only current/past candle data."""
    window = int(window)
    key = ("research_adx", window)
    if key not in cache._cache:
        up_move = cache.high.diff()
        down_move = -cache.low.diff()
        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0.0), up_move, 0.0),
            index=cache.frame.index,
            dtype=np.float64,
        )
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0.0), down_move, 0.0),
            index=cache.frame.index,
            dtype=np.float64,
        )
        atr = cache.atr(window).replace(0.0, np.nan)
        plus_smoothed = plus_dm.ewm(
            alpha=1.0 / window,
            adjust=False,
            min_periods=window,
        ).mean()
        minus_smoothed = minus_dm.ewm(
            alpha=1.0 / window,
            adjust=False,
            min_periods=window,
        ).mean()
        plus_di = 100.0 * plus_smoothed / atr
        minus_di = 100.0 * minus_smoothed / atr
        denominator = (plus_di + minus_di).replace(0.0, np.nan)
        dx = 100.0 * (plus_di - minus_di).abs() / denominator
        adx_value = dx.ewm(
            alpha=1.0 / window,
            adjust=False,
            min_periods=window,
        ).mean()
        cache._cache[key] = (adx_value, plus_di, minus_di)
    return cache._cache[key]  # type: ignore[return-value]


def daily_vwap(cache: IndicatorCache) -> pd.Series:
    """UTC-day anchored VWAP using typical price and candle volume."""
    key = ("research_daily_vwap",)
    if key not in cache._cache:
        day = cache.frame["datetime"].dt.floor("D")
        typical_price = (cache.high + cache.low + cache.close) / 3.0
        cumulative_pv = (typical_price * cache.volume).groupby(day, sort=False).cumsum()
        cumulative_volume = cache.volume.groupby(day, sort=False).cumsum()
        cache._cache[key] = cumulative_pv / cumulative_volume.replace(0.0, np.nan)
    return cache._cache[key]  # type: ignore[return-value]
