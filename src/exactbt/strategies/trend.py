"""
Trend and breakout strategy library converted to ExactBT plugins.

Included strategies:
- Donchian close breakout with EMA regime
- Rolling-range breakout with ATR buffer and EMA regime
- EMA crossover
- EMA-slope pullback continuation

All rolling high/low breakout levels are shifted by one candle. This prevents
lookahead and prevents current-bar high/low from contaminating its own level.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below, regime_filter
from .signal_plugin import PrecomputedSignalPlugin


def donchian_breakout(cache: IndicatorCache, p: dict[str, Any]):
    upper = cache.rolling_high(int(p["lookback"]))
    lower = cache.rolling_low(int(p["lookback"]))
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = crossed_above(cache.close, upper) & long_regime
    short_signal = crossed_below(cache.close, lower) & short_regime
    return long_signal, short_signal


def rolling_range_breakout(cache: IndicatorCache, p: dict[str, Any]):
    upper = cache.rolling_high(int(p["lookback"]))
    lower = cache.rolling_low(int(p["lookback"]))
    atr = cache.atr(int(p["atr_window"]))
    buffer = float(p["breakout_atr_buffer"]) * atr
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = crossed_above(cache.close, upper + buffer) & long_regime
    short_signal = crossed_below(cache.close, lower - buffer) & short_regime
    return long_signal, short_signal


def ema_cross(cache: IndicatorCache, p: dict[str, Any]):
    fast = cache.ema(int(p["fast_ema"]))
    slow = cache.ema(int(p["slow_ema"]))
    long_signal = crossed_above(fast, slow)
    short_signal = crossed_below(fast, slow)
    return long_signal, short_signal


def ema_slope_pullback(cache: IndicatorCache, p: dict[str, Any]):
    trend = cache.ema(int(p["ema_window"]))
    slope = trend - trend.shift(int(p["slope_lookback"]))
    atr = cache.atr(int(p["atr_window"]))
    distance = (cache.close - trend) / atr.replace(0.0, float("nan"))
    max_distance = float(p["pullback_atr"])
    long_signal = (
        (cache.close > trend)
        & (slope > 0.0)
        & (distance >= 0.0)
        & (distance <= max_distance)
        & (distance.shift(1) > max_distance)
        & (cache.close > cache.close.shift(1))
    )
    short_signal = (
        (cache.close < trend)
        & (slope < 0.0)
        & (distance <= 0.0)
        & (distance >= -max_distance)
        & (distance.shift(1) < -max_distance)
        & (cache.close < cache.close.shift(1))
    )
    return long_signal, short_signal


def _valid_ema_cross(config: dict[str, Any]) -> bool:
    return int(config["fast_ema"]) < int(config["slow_ema"])


DONCHIAN_BREAKOUT_PLUGIN = PrecomputedSignalPlugin(
    name="donchian_breakout",
    signal_builder=donchian_breakout,
)
ROLLING_RANGE_BREAKOUT_PLUGIN = PrecomputedSignalPlugin(
    name="rolling_range_breakout",
    signal_builder=rolling_range_breakout,
)
EMA_CROSS_PLUGIN = PrecomputedSignalPlugin(
    name="ema_cross",
    signal_builder=ema_cross,
    validator=_valid_ema_cross,
)
EMA_SLOPE_PULLBACK_PLUGIN = PrecomputedSignalPlugin(
    name="ema_slope_pullback",
    signal_builder=ema_slope_pullback,
)
