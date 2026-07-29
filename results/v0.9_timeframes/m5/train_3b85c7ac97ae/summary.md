# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `71a23cc7f1ca8b15fe806c5371e5fa6329701922b3b0a471b6b72398adfaa96d`
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

No configuration met the non-expectancy gates, including `trades >= 1890`.

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `e6448d0741dcfeaefe480511`
- Trades: `1`
- Expectancy: `1.841078R`
- Gross expectancy: `2.500000R`
- Average cost: `0.658922R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`1` < `1890` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
