"""
Mean-reversion strategy library converted to ExactBT plugins.

Included strategies:
- Bollinger re-entry
- Bollinger wick fade
- Z-score reversion
- RSI extreme recovery

Each function only creates close-confirmed long/short signals. The shared
PrecomputedSignalPlugin supplies ATR-based stop distance, while the exact engine
owns next-open entry, TP, costs, gap handling, both-hit priority, and records.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below, regime_filter
from .signal_plugin import PrecomputedSignalPlugin


def bollinger_reentry(cache: IndicatorCache, p: dict[str, Any]):
    lower, _, upper = cache.bollinger(int(p["window"]), float(p["std_mult"]))
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = (
        crossed_above(cache.close, lower)
        & (cache.close.shift(1) < lower.shift(1))
        & long_regime
    )
    short_signal = (
        crossed_below(cache.close, upper)
        & (cache.close.shift(1) > upper.shift(1))
        & short_regime
    )
    return long_signal, short_signal


def bollinger_fade(cache: IndicatorCache, p: dict[str, Any]):
    lower, _, upper = cache.bollinger(int(p["window"]), float(p["std_mult"]))
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = (cache.low <= lower) & (cache.close > lower) & long_regime
    short_signal = (cache.high >= upper) & (cache.close < upper) & short_regime
    return long_signal, short_signal


def zscore_reversion(cache: IndicatorCache, p: dict[str, Any]):
    mean = cache.sma(int(p["window"]))
    std = cache.std(int(p["window"])).replace(0.0, float("nan"))
    zscore = (cache.close - mean) / std
    threshold = float(p["zscore_threshold"])
    long_signal = crossed_above(zscore, -threshold)
    short_signal = crossed_below(zscore, threshold)
    return long_signal, short_signal


def rsi_extreme(cache: IndicatorCache, p: dict[str, Any]):
    value = cache.rsi(int(p["rsi_window"]))
    level = float(p["level"])
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = (
        crossed_above(value, level)
        & (value.shift(1) < level)
        & long_regime
    )
    short_level = 100.0 - level
    short_signal = (
        crossed_below(value, short_level)
        & (value.shift(1) > short_level)
        & short_regime
    )
    return long_signal, short_signal


BOLLINGER_REENTRY_PLUGIN = PrecomputedSignalPlugin(
    name="bollinger_reentry",
    signal_builder=bollinger_reentry,
)
BOLLINGER_FADE_PLUGIN = PrecomputedSignalPlugin(
    name="bollinger_fade",
    signal_builder=bollinger_fade,
)
ZSCORE_REVERSION_PLUGIN = PrecomputedSignalPlugin(
    name="zscore_reversion",
    signal_builder=zscore_reversion,
)
RSI_EXTREME_PLUGIN = PrecomputedSignalPlugin(
    name="rsi_extreme",
    signal_builder=rsi_extreme,
)
