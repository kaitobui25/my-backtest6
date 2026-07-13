# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **8**
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

No configuration met the non-expectancy gates, including `trades >= 80`.

## Best raw result — diagnostic only

- Strategy: `momentum_volume`
- Config ID: `9fc41b8bed85d386ff9c7f57`
- Trades: `62`
- Expectancy: `0.155981R`
- Gross expectancy: `0.243077R`
- Average cost: `0.087096R`
- Profit factor: `1.297095`
- Max drawdown: `9.632317R`

**REJECTED: insufficient sample (`62` < `80` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
