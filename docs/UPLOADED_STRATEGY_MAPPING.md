# Mapping from uploaded files to ExactBT plugins

| Uploaded file/function | ExactBT plugin path |
|---|---|
| `mean_reversion.py / bollinger_reentry` | `exactbt.strategies.mean_reversion:BOLLINGER_REENTRY_PLUGIN` |
| `mean_reversion.py / bollinger_fade` | `exactbt.strategies.mean_reversion:BOLLINGER_FADE_PLUGIN` |
| `mean_reversion.py / zscore_reversion` | `exactbt.strategies.mean_reversion:ZSCORE_REVERSION_PLUGIN` |
| `mean_reversion.py / rsi_extreme` | `exactbt.strategies.mean_reversion:RSI_EXTREME_PLUGIN` |
| `momentum.py / rsi_momentum` | `exactbt.strategies.momentum:RSI_MOMENTUM_PLUGIN` |
| `momentum.py / roc_momentum` | `exactbt.strategies.momentum:ROC_MOMENTUM_PLUGIN` |
| `momentum.py / macd_momentum` | `exactbt.strategies.momentum:MACD_MOMENTUM_PLUGIN` |
| `trend.py / donchian_breakout` | `exactbt.strategies.trend:DONCHIAN_BREAKOUT_PLUGIN` |
| `trend.py / rolling_range_breakout` | `exactbt.strategies.trend:ROLLING_RANGE_BREAKOUT_PLUGIN` |
| `trend.py / ema_cross` | `exactbt.strategies.trend:EMA_CROSS_PLUGIN` |
| `trend.py / ema_slope_pullback` | `exactbt.strategies.trend:EMA_SLOPE_PULLBACK_PLUGIN` |
| `volatility.py / atr_expansion_breakout` | `exactbt.strategies.volatility:ATR_EXPANSION_BREAKOUT_PLUGIN` |
| `volatility.py / squeeze_breakout` | `exactbt.strategies.volatility:SQUEEZE_BREAKOUT_PLUGIN` |
| `volume.py / breakout_volume` | `exactbt.strategies.volume:BREAKOUT_VOLUME_PLUGIN` |
| `volume.py / momentum_volume` | `exactbt.strategies.volume:MOMENTUM_VOLUME_PLUGIN` |

## Conversion differences that are intentional

- Imports now use `exactbt`, not `btsearch`.
- Signals are precomputed and cached, then read by the Numba exact kernel.
- Rolling breakout highs/lows are shifted one candle to prevent lookahead.
- A shared ATR-distance stop was added because the uploaded functions did not
  specify stop loss.
- RR, ATR stop, max hold and side are execution parameters and do not cause
  signal indicators to be recalculated.
