# Strategy library

`config/search.yaml` enables all 17 included strategy families and currently
expands to **23,796 exact configurations**.

## Stateful / custom execution-aware setup logic

| Strategy | Core signal |
|---|---|
| `liquidity_sweep_reclaim` | Sweep previous-day high/low and reclaim |
| `donchian_ema_atr` | Donchian breakout while on the correct side of EMA |

## Mean reversion

| Strategy | Core signal |
|---|---|
| `bollinger_reentry` | Close crosses back inside a Bollinger band |
| `bollinger_fade` | Wick touches/exceeds band, close returns inside |
| `zscore_reversion` | Z-score crosses back through an extreme threshold |
| `rsi_extreme` | RSI recovers from oversold/overbought with EMA regime |

## Momentum

| Strategy | Core signal |
|---|---|
| `rsi_momentum` | RSI crosses momentum threshold with EMA regime |
| `roc_momentum` | ROC crosses positive/negative threshold with EMA regime |
| `macd_momentum` | MACD line crosses signal line with histogram confirmation |

## Trend / breakout

| Strategy | Core signal |
|---|---|
| `donchian_breakout` | Close crosses prior rolling high/low with EMA regime |
| `rolling_range_breakout` | Close crosses prior range plus ATR buffer |
| `ema_cross` | Fast EMA crosses slow EMA |
| `ema_slope_pullback` | Pullback toward a sloping EMA then continuation |

## Volatility

| Strategy | Core signal |
|---|---|
| `atr_expansion_breakout` | Rolling breakout during ATR expansion |
| `squeeze_breakout` | Breakout after low Bollinger bandwidth |

## Volume-confirmed

| Strategy | Core signal |
|---|---|
| `breakout_volume` | Rolling breakout with relative-volume confirmation |
| `momentum_volume` | ROC threshold cross with relative-volume confirmation |

## Shared execution controls

The 15 simple indicator strategies use this YAML anchor:

```yaml
simple_strategy_execution: &simple_execution
  atr_stop_window: [14, 21]
  atr_stop_multiplier: [1.0, 1.5, 2.0]
  risk_reward: [1.5, 2.0, 2.5]
  max_hold_bars: [0, 96]
  side: [both]
```

Change this once to change the execution grid for all of them. This does **not**
make their execution approximate: every expanded combination still runs through
the authoritative exact kernel.

## Important interpretation details

- Signal is confirmed at candle close; entry is next candle open.
- Breakout high/low levels are shifted one candle to prevent lookahead.
- ATR is Wilder-smoothed.
- RSI is Wilder-smoothed.
- ROC thresholds are percentage points (`1.0` means `1%`).
- Bollinger rolling standard deviation uses `ddof=0`.
- If both long and short signals occur on one candle, no trade is emitted.
- The 15 converted indicator strategies use ATR-distance stops. Their original
  uploaded functions only produced entry signals and did not define SL.
