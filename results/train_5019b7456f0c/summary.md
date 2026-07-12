# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **10,224**
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

No configuration met the non-expectancy gates, including `trades >= 300`.

## Best raw result — diagnostic only

- Strategy: `rolling_sweep_reclaim`
- Config ID: `371ac17215b6fafae1b079bd`
- Trades: `22`
- Expectancy: `0.303171R`
- Gross expectancy: `0.607272R`
- Average cost: `0.304101R`
- Profit factor: `1.821084`
- Max drawdown: `2.027499R`

**REJECTED: insufficient sample (`22` < `300` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
