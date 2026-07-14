# TradingView — ATR Expansion Breakout

File:

```text
atr_expansion_breakout.pine
```

## Add to TradingView

1. Open a standard-candle BTC futures chart.
2. Select the **15-minute** timeframe used by the ExactBT research.
3. Open **Pine Editor**.
4. Paste the complete contents of `atr_expansion_breakout.pine`.
5. Click **Save**, then **Add to chart**.
6. Open **Strategy Tester** to inspect trades and performance.

## Default configuration

The Pine inputs default to:

```text
strategy:             atr_expansion_breakout
atr_mean_window:      50
atr_window:           14
atr_stop_window:      14
atr_stop_multiplier:  4.0
expansion_mult:       1.25
lookback:             192
max_hold_bars:        384
risk_reward:          4.0
side:                 both
```

The script also defaults to cancelling a signal whose pending next-open entry
would cross into a new UTC calendar day, matching the current ExactBT engine
configuration.

## Logic mapped from ExactBT

```text
ATR expansion:
ATR(14) > SMA(ATR(14), 50) × 1.25

Long signal:
Close crosses above the highest High of the previous 192 candles.

Short signal:
Close crosses below the lowest Low of the previous 192 candles.

Entry:
Market entry at the next candle Open.

Stop distance:
ATR_stop(14) from the signal candle × 4.0.

Target:
4.0 × stop distance from the actual entry price.

Time exit:
Close a surviving trade after 384 bars.

Position rules:
One position only; no pyramiding; no setup scanning while a position is open;
no same-candle re-entry after an exit.
```

The script includes a custom ATR calculation matching pandas:

```text
ewm(alpha = 1 / window, adjust = false, min_periods = window)
```

This is intentionally used instead of relying on Pine's normal ATR seed.

## Costs and unavoidable TradingView differences

The strategy declaration includes the ExactBT fee default:

```text
commission = 0.05% per filled order side
```

ExactBT additionally applies `0.02%` slippage per side. TradingView's strategy
property models slippage as a fixed number of ticks rather than a percentage of
price, so the script does not hard-code a misleading BTC-specific tick value.
Set an appropriate tick slippage manually in **Strategy settings → Properties**
when needed.

ExactBT uses a conservative rule when SL and TP are both touched in one candle:

```text
SL wins.
```

TradingView instead resolves the order sequence using its broker-emulator
intrabar assumptions, or lower-timeframe data when Bar Magnifier is enabled.
Consequently, TradingView results are useful for chart inspection, alerts and an
independent approximation, but they are not guaranteed to be trade-for-trade
identical to ExactBT.

Use standard candles. Heikin Ashi, Renko and other synthetic chart types can
produce fills based on synthetic OHLC values.
