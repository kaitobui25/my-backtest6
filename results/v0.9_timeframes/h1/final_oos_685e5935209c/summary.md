# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **56**
- Configs meeting non-expectancy gates: **0**
- Configs passing full selection: **0**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

No configuration met the non-expectancy gates, including `trades >= 45`.

## Best raw result — diagnostic only

- Strategy: `rolling_range_breakout`
- Config ID: `6079a7e7ffe70d247052b938`
- Trades: `85`
- Expectancy: `0.060216R`
- Gross expectancy: `0.147994R`
- Average cost: `0.087777R`
- Profit factor: `1.078952`
- Max drawdown: `21.793296R`

## Best eligible by strategy

No strategy has a sample-eligible configuration.
