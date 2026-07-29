# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **34,992**
- Configs meeting non-expectancy gates: **11,329**
- Configs passing full selection: **11,251**
- Eligible near threshold: **78**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `rolling_range_breakout`
- Config ID: `20eb4478750f4dd7c1b3e996`
- Trades: `48`
- Expectancy: `0.730316R`
- Gross expectancy: `0.794071R`
- Average cost: `0.063755R`
- Profit factor: `2.443574`
- Max drawdown: `3.252782R`

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `6cb83d3f7b9ab6448a13a915`
- Trades: `1`
- Expectancy: `2.471423R`
- Gross expectancy: `2.500000R`
- Average cost: `0.028577R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`1` < `40` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 48 | 0.7303 | 0.7941 | 0.0638 | 2.444 | 3.3 |
| adx_ema_pullback | 60 | 0.3979 | 0.4583 | 0.0604 | 1.900 | 5.2 |
