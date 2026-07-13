# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **6,048**
- Configs meeting non-expectancy gates: **691**
- Configs passing full selection: **684**
- Eligible near threshold: **7**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `5c211de3e5c2671087a0f924`
- Trades: `78`
- Expectancy: `0.489790R`
- Gross expectancy: `0.540323R`
- Average cost: `0.050533R`
- Profit factor: `1.775894`
- Max drawdown: `10.468329R`

## Best raw result — diagnostic only

- Strategy: `squeeze_breakout`
- Config ID: `2b74b6e7fbaf65a40ac2da14`
- Trades: `8`
- Expectancy: `1.159162R`
- Gross expectancy: `1.210765R`
- Average cost: `0.051604R`
- Profit factor: `3.218135`
- Max drawdown: `3.155611R`

**REJECTED: insufficient sample (`8` < `75` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 78 | 0.4898 | 0.5403 | 0.0505 | 1.776 | 10.5 |
| squeeze_breakout | 83 | 0.3370 | 0.4034 | 0.0664 | 1.452 | 14.6 |
| donchian_ema_atr | 124 | 0.3335 | 0.3983 | 0.0648 | 1.452 | 9.3 |
| donchian_breakout | 120 | 0.3277 | 0.3897 | 0.0621 | 1.446 | 9.3 |
