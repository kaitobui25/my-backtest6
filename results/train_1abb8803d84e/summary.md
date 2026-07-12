# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **8,208**
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

- Strategy: `rsi_extreme`
- Config ID: `795f785a628faa0abb813946`
- Trades: `3`
- Expectancy: `0.792725R`
- Gross expectancy: `1.000000R`
- Average cost: `0.207275R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`3` < `300` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
