# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **1,461**
- Configs meeting non-expectancy gates: **184**
- Configs passing full selection: **184**
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
- Config ID: `c968532ac3b7fe411f3825d8`
- Trades: `38`
- Expectancy: `0.560869R`
- Gross expectancy: `0.657895R`
- Average cost: `0.097026R`
- Profit factor: `1.975673`
- Max drawdown: `7.557100R`

## Best raw result — diagnostic only

- Strategy: `rolling_range_breakout`
- Config ID: `c968532ac3b7fe411f3825d8`
- Trades: `38`
- Expectancy: `0.560869R`
- Gross expectancy: `0.657895R`
- Average cost: `0.097026R`
- Profit factor: `1.975673`
- Max drawdown: `7.557100R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 38 | 0.5609 | 0.6579 | 0.0970 | 1.976 | 7.6 |
| adx_ema_pullback | 27 | 0.3643 | 0.4591 | 0.0948 | 1.680 | 6.6 |
