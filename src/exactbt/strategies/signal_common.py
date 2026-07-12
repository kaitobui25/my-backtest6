"""
Shared signal helpers for close-confirmed indicator strategies.

These functions create boolean pandas Series outside the exact execution loop.
They never enter or exit a position. The common engine later converts a signal
at candle i into a pending order for candle i+1 and applies the authoritative
SL/TP, fee, slippage, both-hit, gap, and trade-record rules.
"""

from __future__ import annotations

import pandas as pd

from exactbt.indicators import IndicatorCache


def crossed_above(left: pd.Series, right: pd.Series | float) -> pd.Series:
    """True only on the first candle where left moves from <= right to > right."""
    if isinstance(right, pd.Series):
        return (left > right) & (left.shift(1) <= right.shift(1))
    return (left > right) & (left.shift(1) <= right)


def crossed_below(left: pd.Series, right: pd.Series | float) -> pd.Series:
    """True only on the first candle where left moves from >= right to < right."""
    if isinstance(right, pd.Series):
        return (left < right) & (left.shift(1) >= right.shift(1))
    return (left < right) & (left.shift(1) >= right)


def regime_filter(cache: IndicatorCache, ema_window: int) -> tuple[pd.Series, pd.Series]:
    """Simple trend regime: long above EMA, short below EMA."""
    trend = cache.ema(int(ema_window))
    return cache.close > trend, cache.close < trend


def normalize_signals(
    long_signal: pd.Series,
    short_signal: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """Fill missing values and reject a candle where both directions fire."""
    long_clean = long_signal.fillna(False).astype(bool)
    short_clean = short_signal.fillna(False).astype(bool)
    ambiguous = long_clean & short_clean
    return long_clean & ~ambiguous, short_clean & ~ambiguous
