# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **2,598**
- Configs meeting non-expectancy gates: **764**
- Configs passing full selection: **764**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `rolling_range_breakout`
- Config ID: `9285aff34091b99e14273436`
- Trades: `16`
- Expectancy: `0.542377R`
- Gross expectancy: `0.635070R`
- Average cost: `0.092694R`
- Profit factor: `1.886180`
- Max drawdown: `4.408275R`

## Best raw result — diagnostic only

- Strategy: `rolling_range_breakout`
- Config ID: `27a42d0860f81d2843029ce0`
- Trades: `10`
- Expectancy: `0.556160R`
- Gross expectancy: `0.613752R`
- Average cost: `0.057592R`
- Profit factor: `2.040576`
- Max drawdown: `3.180330R`

**REJECTED: insufficient sample (`10` < `12` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 16 | 0.5424 | 0.6351 | 0.0927 | 1.886 | 4.4 |
| adx_ema_pullback | 12 | 0.3704 | 0.4583 | 0.0880 | 1.583 | 3.3 |
