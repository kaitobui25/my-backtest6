# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **4,860**
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

- Strategy: `liquidity_sweep_reclaim`
- Config ID: `caf774f9cbe44fa0a510c0dc`
- Trades: `1058`
- Expectancy: `-0.211937R`
- Gross expectancy: `0.124601R`
- Average cost: `0.336539R`
- Profit factor: `0.730831`
- Max drawdown: `225.550864R`

## Best eligible by strategy

No strategy has a sample-eligible configuration.
