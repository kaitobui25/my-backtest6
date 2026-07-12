"""
Reusable, cached technical indicators for simple signal strategies.

This module runs outside the Numba execution loop. Every indicator is computed
once per unique parameter value and then reused by every configuration that
needs it. Signals are evaluated only with information available at candle close;
entries remain the responsibility of the exact engine on the next candle open.

Definitions used by this project:
- ATR and RSI use Wilder-style exponential smoothing.
- ROC is expressed in percentage points, e.g. 1.5 means +1.5%.
- Bollinger standard deviation uses ddof=0.
- Rolling breakout highs/lows are shifted one candle to avoid lookahead and the
  impossible comparison of close against a channel containing the same bar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .types import CandleData


@dataclass
class IndicatorCache:
    """Lazy pandas indicator cache shared while one strategy plugin is prepared."""

    candles: CandleData
    _cache: dict[tuple[object, ...], object] = field(default_factory=dict)

    @property
    def frame(self) -> pd.DataFrame:
        return self.candles.frame

    @property
    def open(self) -> pd.Series:
        return self.frame["open"]

    @property
    def high(self) -> pd.Series:
        return self.frame["high"]

    @property
    def low(self) -> pd.Series:
        return self.frame["low"]

    @property
    def close(self) -> pd.Series:
        return self.frame["close"]

    @property
    def volume(self) -> pd.Series:
        return self.frame["volume"]

    def sma(self, window: int) -> pd.Series:
        key = ("sma", int(window))
        if key not in self._cache:
            self._cache[key] = self.close.rolling(window, min_periods=window).mean()
        return self._cache[key]  # type: ignore[return-value]

    def ema(self, window: int) -> pd.Series:
        key = ("ema", int(window))
        if key not in self._cache:
            self._cache[key] = self.close.ewm(
                span=window,
                adjust=False,
                min_periods=window,
            ).mean()
        return self._cache[key]  # type: ignore[return-value]

    def std(self, window: int) -> pd.Series:
        key = ("std", int(window))
        if key not in self._cache:
            self._cache[key] = self.close.rolling(
                window,
                min_periods=window,
            ).std(ddof=0)
        return self._cache[key]  # type: ignore[return-value]

    def atr(self, window: int) -> pd.Series:
        key = ("atr", int(window))
        if key not in self._cache:
            previous_close = self.close.shift(1)
            true_range = pd.concat(
                [
                    self.high - self.low,
                    (self.high - previous_close).abs(),
                    (self.low - previous_close).abs(),
                ],
                axis=1,
            ).max(axis=1)
            self._cache[key] = true_range.ewm(
                alpha=1.0 / window,
                adjust=False,
                min_periods=window,
            ).mean()
        return self._cache[key]  # type: ignore[return-value]

    def rsi(self, window: int) -> pd.Series:
        key = ("rsi", int(window))
        if key not in self._cache:
            delta = self.close.diff()
            gain = delta.clip(lower=0.0)
            loss = -delta.clip(upper=0.0)
            avg_gain = gain.ewm(
                alpha=1.0 / window,
                adjust=False,
                min_periods=window,
            ).mean()
            avg_loss = loss.ewm(
                alpha=1.0 / window,
                adjust=False,
                min_periods=window,
            ).mean()
            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - 100.0 / (1.0 + rs)
            rsi = rsi.where(avg_loss != 0.0, 100.0)
            rsi = rsi.where(~((avg_gain == 0.0) & (avg_loss == 0.0)), 50.0)
            self._cache[key] = rsi
        return self._cache[key]  # type: ignore[return-value]

    def roc(self, window: int) -> pd.Series:
        key = ("roc", int(window))
        if key not in self._cache:
            self._cache[key] = (self.close / self.close.shift(window) - 1.0) * 100.0
        return self._cache[key]  # type: ignore[return-value]

    def macd(
        self,
        fast: int,
        slow: int,
        signal: int,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        key = ("macd", int(fast), int(slow), int(signal))
        if key not in self._cache:
            fast_ema = self.close.ewm(
                span=fast,
                adjust=False,
                min_periods=fast,
            ).mean()
            slow_ema = self.close.ewm(
                span=slow,
                adjust=False,
                min_periods=slow,
            ).mean()
            macd_line = fast_ema - slow_ema
            signal_line = macd_line.ewm(
                span=signal,
                adjust=False,
                min_periods=signal,
            ).mean()
            histogram = macd_line - signal_line
            self._cache[key] = (macd_line, signal_line, histogram)
        return self._cache[key]  # type: ignore[return-value]

    def bollinger(
        self,
        window: int,
        std_mult: float,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        key = ("bollinger", int(window), float(std_mult))
        if key not in self._cache:
            middle = self.sma(window)
            deviation = self.std(window) * float(std_mult)
            self._cache[key] = (middle - deviation, middle, middle + deviation)
        return self._cache[key]  # type: ignore[return-value]

    def rolling_high(self, window: int) -> pd.Series:
        key = ("rolling_high_shifted", int(window))
        if key not in self._cache:
            self._cache[key] = self.high.rolling(
                window,
                min_periods=window,
            ).max().shift(1)
        return self._cache[key]  # type: ignore[return-value]

    def rolling_low(self, window: int) -> pd.Series:
        key = ("rolling_low_shifted", int(window))
        if key not in self._cache:
            self._cache[key] = self.low.rolling(
                window,
                min_periods=window,
            ).min().shift(1)
        return self._cache[key]  # type: ignore[return-value]

    def volume_mean(self, window: int) -> pd.Series:
        key = ("volume_mean", int(window))
        if key not in self._cache:
            self._cache[key] = self.volume.rolling(
                window,
                min_periods=window,
            ).mean()
        return self._cache[key]  # type: ignore[return-value]

    def bandwidth(self, window: int, std_mult: float) -> pd.Series:
        key = ("bandwidth", int(window), float(std_mult))
        if key not in self._cache:
            lower, middle, upper = self.bollinger(window, std_mult)
            denominator = middle.abs().replace(0.0, np.nan)
            self._cache[key] = (upper - lower) / denominator
        return self._cache[key]  # type: ignore[return-value]
