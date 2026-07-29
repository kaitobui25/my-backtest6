# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **836**
- Configs meeting non-expectancy gates: **56**
- Configs passing full selection: **56**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `rolling_range_breakout`
- Config ID: `084dabfac8d66dba9f332524`
- Trades: `89`
- Expectancy: `0.306105R`
- Gross expectancy: `0.388032R`
- Average cost: `0.081927R`
- Profit factor: `1.458377`
- Max drawdown: `7.622293R`

## Best raw result — diagnostic only

- Strategy: `rolling_range_breakout`
- Config ID: `084dabfac8d66dba9f332524`
- Trades: `89`
- Expectancy: `0.306105R`
- Gross expectancy: `0.388032R`
- Average cost: `0.081927R`
- Profit factor: `1.458377`
- Max drawdown: `7.622293R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 89 | 0.3061 | 0.3880 | 0.0819 | 1.458 | 7.6 |
