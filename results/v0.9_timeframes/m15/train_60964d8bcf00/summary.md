# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `308b94395ac152fb9a99956479ae020ac54f24fc08e89a474811ab7492197e86`
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

No configuration met the non-expectancy gates, including `trades >= 630`.

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `b41792170392610118d91720`
- Trades: `1`
- Expectancy: `2.341140R`
- Gross expectancy: `2.500000R`
- Average cost: `0.158860R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`1` < `630` trades).**

## Best eligible by strategy

No strategy has a sample-eligible configuration.
