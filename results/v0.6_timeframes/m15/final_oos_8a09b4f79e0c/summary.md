# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `308b94395ac152fb9a99956479ae020ac54f24fc08e89a474811ab7492197e86`
- Exact configs evaluated: **9**
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

- Strategy: `atr_expansion_breakout`
- Config ID: `27e39d4f0c32f336587d2fa1`
- Trades: `109`
- Expectancy: `-0.060372R`
- Gross expectancy: `0.034932R`
- Average cost: `0.095304R`
- Profit factor: `0.910238`
- Max drawdown: `26.861887R`

## Best eligible by strategy

No strategy has a sample-eligible configuration.
