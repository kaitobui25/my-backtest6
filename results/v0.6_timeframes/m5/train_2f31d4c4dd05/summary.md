# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `71a23cc7f1ca8b15fe806c5371e5fa6329701922b3b0a471b6b72398adfaa96d`
- Exact configs evaluated: **6,048**
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

No configuration met the non-expectancy gates, including `trades >= 900`.

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `63e818cb912970d37741d0ed`
- Trades: `239`
- Expectancy: `0.171274R`
- Gross expectancy: `0.311248R`
- Average cost: `0.139974R`
- Profit factor: `1.292328`
- Max drawdown: `7.886969R`

**REJECTED: insufficient sample (`239` < `900` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
