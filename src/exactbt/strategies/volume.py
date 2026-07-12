"""
Volume-confirmed strategy library converted to ExactBT plugins.

Included strategies:
- Rolling breakout with relative-volume confirmation
- ROC momentum with relative-volume confirmation

Volume confirmation compares current candle volume with the rolling mean times
`volume_mult`. Entries still occur at the following candle open.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below
from .signal_plugin import PrecomputedSignalPlugin


def breakout_volume(cache: IndicatorCache, p: dict[str, Any]):
    volume_ok = cache.volume > (
        cache.volume_mean(int(p["volume_window"])) * float(p["volume_mult"])
    )
    upper = cache.rolling_high(int(p["lookback"]))
    lower = cache.rolling_low(int(p["lookback"]))
    long_signal = crossed_above(cache.close, upper) & volume_ok
    short_signal = crossed_below(cache.close, lower) & volume_ok
    return long_signal, short_signal


def momentum_volume(cache: IndicatorCache, p: dict[str, Any]):
    value = cache.roc(int(p["roc_window"]))
    threshold = float(p["threshold"])
    volume_ok = cache.volume > (
        cache.volume_mean(int(p["volume_window"])) * float(p["volume_mult"])
    )
    long_signal = crossed_above(value, threshold) & volume_ok
    short_signal = crossed_below(value, -threshold) & volume_ok
    return long_signal, short_signal


BREAKOUT_VOLUME_PLUGIN = PrecomputedSignalPlugin(
    name="breakout_volume",
    signal_builder=breakout_volume,
)
MOMENTUM_VOLUME_PLUGIN = PrecomputedSignalPlugin(
    name="momentum_volume",
    signal_builder=momentum_volume,
)
