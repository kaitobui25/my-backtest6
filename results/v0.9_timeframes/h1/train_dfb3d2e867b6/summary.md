# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **34,992**
- Configs meeting non-expectancy gates: **840**
- Configs passing full selection: **836**
- Eligible near threshold: **4**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `rolling_range_breakout`
- Config ID: `7b0e93f063f33c4eaf3c527d`
- Trades: `161`
- Expectancy: `0.329136R`
- Gross expectancy: `0.421145R`
- Average cost: `0.092009R`
- Profit factor: `1.592223`
- Max drawdown: `7.465435R`

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `ee22c3d18c27f1df0fb38a46`
- Trades: `3`
- Expectancy: `2.440989R`
- Gross expectancy: `2.500000R`
- Average cost: `0.059011R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`3` < `158` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 161 | 0.3291 | 0.4211 | 0.0920 | 1.592 | 7.5 |
| adx_ema_pullback | 194 | 0.2129 | 0.3359 | 0.1231 | 1.354 | 9.3 |
