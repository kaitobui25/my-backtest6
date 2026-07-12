"""
Momentum strategy library converted to ExactBT plugins.

Included strategies:
- RSI momentum threshold cross
- Rate-of-change momentum threshold cross
- MACD line/signal momentum cross

ROC thresholds use percentage points. For example threshold=1.0 means a
one-percent rate of change over the selected lookback.
"""

from __future__ import annotations

from typing import Any

from exactbt.indicators import IndicatorCache
from .signal_common import crossed_above, crossed_below, regime_filter
from .signal_plugin import PrecomputedSignalPlugin


def rsi_momentum(cache: IndicatorCache, p: dict[str, Any]):
    value = cache.rsi(int(p["rsi_window"]))
    threshold = float(p["threshold"])
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = crossed_above(value, threshold) & long_regime
    short_signal = crossed_below(value, 100.0 - threshold) & short_regime
    return long_signal, short_signal


def roc_momentum(cache: IndicatorCache, p: dict[str, Any]):
    value = cache.roc(int(p["roc_window"]))
    threshold = float(p["threshold"])
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = crossed_above(value, threshold) & long_regime
    short_signal = crossed_below(value, -threshold) & short_regime
    return long_signal, short_signal


def macd_momentum(cache: IndicatorCache, p: dict[str, Any]):
    macd_line, signal_line, histogram = cache.macd(
        int(p["fast"]),
        int(p["slow"]),
        int(p["signal"]),
    )
    long_regime, short_regime = regime_filter(cache, int(p["regime_ema"]))
    long_signal = (
        crossed_above(macd_line, signal_line)
        & (histogram > 0.0)
        & long_regime
    )
    short_signal = (
        crossed_below(macd_line, signal_line)
        & (histogram < 0.0)
        & short_regime
    )
    return long_signal, short_signal


def _valid_macd(config: dict[str, Any]) -> bool:
    return int(config["fast"]) < int(config["slow"])


RSI_MOMENTUM_PLUGIN = PrecomputedSignalPlugin(
    name="rsi_momentum",
    signal_builder=rsi_momentum,
)
ROC_MOMENTUM_PLUGIN = PrecomputedSignalPlugin(
    name="roc_momentum",
    signal_builder=roc_momentum,
)
MACD_MOMENTUM_PLUGIN = PrecomputedSignalPlugin(
    name="macd_momentum",
    signal_builder=macd_momentum,
    validator=_valid_macd,
)
