"""Focused OHLCV strategy families for ExactBT research v0.3.

These are deliberately not cosmetic indicator variations:
- ADX + dual-EMA pullback reclaim: trend-continuation after a real pullback.
- UTC daily VWAP reclaim: intraday location + trend + relative-volume filter.

Signals are close-confirmed and execute at the next candle open through the
existing exact kernel. Stops remain the common ATR-distance model.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below
from .signal_plugin import PrecomputedSignalPlugin
from .strategy_indicators import adx, daily_vwap


def adx_ema_pullback(cache: IndicatorCache, p: dict[str, Any]):
    fast = cache.ema(int(p["fast_ema"]))
    slow = cache.ema(int(p["slow_ema"]))
    adx_value, plus_di, minus_di = adx(cache, int(p["adx_window"]))

    threshold = float(p["adx_threshold"])
    lookback = int(p["pullback_lookback"])
    require_di = bool(p.get("require_di", True))

    touched_fast_long = (
        (cache.low.shift(1) <= fast.shift(1))
        .rolling(lookback, min_periods=1)
        .max()
        .fillna(0.0)
        .astype(bool)
    )
    touched_fast_short = (
        (cache.high.shift(1) >= fast.shift(1))
        .rolling(lookback, min_periods=1)
        .max()
        .fillna(0.0)
        .astype(bool)
    )

    long_quality = (plus_di > minus_di) if require_di else True
    short_quality = (minus_di > plus_di) if require_di else True

    long_signal = (
        crossed_above(cache.close, fast)
        & touched_fast_long
        & (fast > slow)
        & (cache.close > slow)
        & (adx_value >= threshold)
        & long_quality
        & (cache.close > cache.open)
    )
    short_signal = (
        crossed_below(cache.close, fast)
        & touched_fast_short
        & (fast < slow)
        & (cache.close < slow)
        & (adx_value >= threshold)
        & short_quality
        & (cache.close < cache.open)
    )
    return long_signal, short_signal


def daily_vwap_reclaim(cache: IndicatorCache, p: dict[str, Any]):
    vwap = daily_vwap(cache)
    trend = cache.ema(int(p["regime_ema"]))
    volume_mean = cache.volume_mean(int(p["volume_window"]))
    volume_ok = cache.volume >= volume_mean * float(p["volume_mult"])

    slope_lookback = int(p["vwap_slope_lookback"])
    vwap_slope = vwap - vwap.shift(slope_lookback)
    bar_in_day = cache.frame.groupby(
        cache.frame["datetime"].dt.floor("D"), sort=False
    ).cumcount()
    mature_session = bar_in_day >= int(p["min_bars_after_reset"])

    long_signal = (
        crossed_above(cache.close, vwap)
        & (cache.close > trend)
        & (vwap_slope > 0.0)
        & volume_ok
        & mature_session
    )
    short_signal = (
        crossed_below(cache.close, vwap)
        & (cache.close < trend)
        & (vwap_slope < 0.0)
        & volume_ok
        & mature_session
    )
    return long_signal, short_signal


def _valid_adx_pullback(config: dict[str, Any]) -> bool:
    return (
        int(config["fast_ema"]) < int(config["slow_ema"])
        and int(config["pullback_lookback"]) >= 1
        and float(config["adx_threshold"]) > 0.0
    )


ADX_EMA_PULLBACK_PLUGIN = PrecomputedSignalPlugin(
    name="adx_ema_pullback",
    signal_builder=adx_ema_pullback,
    validator=_valid_adx_pullback,
)

DAILY_VWAP_RECLAIM_PLUGIN = PrecomputedSignalPlugin(
    name="daily_vwap_reclaim",
    signal_builder=daily_vwap_reclaim,
)
