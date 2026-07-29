# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `665743d2c92cb17b3336aaff83bc589ee91267a6be47552cbe824ffb4d0e0bbc`
- Exact configs evaluated: **34,992**
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

No configuration met the non-expectancy gates, including `trades >= 315`.

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `ebcf20855612decbeb3b9e7b`
- Trades: `1`
- Expectancy: `2.433127R`
- Gross expectancy: `2.500000R`
- Average cost: `0.066873R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`1` < `315` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
