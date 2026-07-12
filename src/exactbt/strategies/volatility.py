"""
Volatility strategy library converted to ExactBT plugins.

Included strategies:
- ATR-expansion rolling breakout
- Bollinger-bandwidth squeeze then rolling breakout

The squeeze detector only uses bandwidth information available before the
breakout candle. Breakout highs/lows are shifted one candle.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below
from .signal_plugin import PrecomputedSignalPlugin


def atr_expansion_breakout(cache: IndicatorCache, p: dict[str, Any]):
    atr = cache.atr(int(p["atr_window"]))
    atr_mean_window = int(p["atr_mean_window"])
    atr_mean = atr.rolling(
        atr_mean_window,
        min_periods=atr_mean_window,
    ).mean()
    expansion = atr > atr_mean * float(p["expansion_mult"])
    upper = cache.rolling_high(int(p["lookback"]))
    lower = cache.rolling_low(int(p["lookback"]))
    long_signal = crossed_above(cache.close, upper) & expansion
    short_signal = crossed_below(cache.close, lower) & expansion
    return long_signal, short_signal


def squeeze_breakout(cache: IndicatorCache, p: dict[str, Any]):
    bandwidth = cache.bandwidth(int(p["bb_window"]), float(p["std_mult"]))
    lookback = int(p["bandwidth_lookback"])
    threshold = bandwidth.rolling(
        lookback,
        min_periods=lookback,
    ).quantile(float(p["quantile"]))
    squeeze_recent = (
        (bandwidth.shift(1) <= threshold.shift(1))
        .rolling(int(p["squeeze_memory"]), min_periods=1)
        .max()
        .fillna(0.0)
        .astype(bool)
    )
    upper = cache.rolling_high(int(p["breakout_lookback"]))
    lower = cache.rolling_low(int(p["breakout_lookback"]))
    long_signal = crossed_above(cache.close, upper) & squeeze_recent
    short_signal = crossed_below(cache.close, lower) & squeeze_recent
    return long_signal, short_signal


ATR_EXPANSION_BREAKOUT_PLUGIN = PrecomputedSignalPlugin(
    name="atr_expansion_breakout",
    signal_builder=atr_expansion_breakout,
)
SQUEEZE_BREAKOUT_PLUGIN = PrecomputedSignalPlugin(
    name="squeeze_breakout",
    signal_builder=squeeze_breakout,
)
