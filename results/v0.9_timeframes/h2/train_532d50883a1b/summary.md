# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **34,992**
- Configs meeting non-expectancy gates: **4,917**
- Configs passing full selection: **4,902**
- Eligible near threshold: **15**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `rolling_range_breakout`
- Config ID: `9b8f73b2ce939c7945c29000`
- Trades: `113`
- Expectancy: `0.507518R`
- Gross expectancy: `0.595855R`
- Average cost: `0.088337R`
- Profit factor: `1.894097`
- Max drawdown: `9.016977R`

## Best raw result — diagnostic only

- Strategy: `ema_slope_pullback`
- Config ID: `81dbe3bd462c0b01b9e08493`
- Trades: `1`
- Expectancy: `2.471260R`
- Gross expectancy: `2.500000R`
- Average cost: `0.028740R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`1` < `79` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| rolling_range_breakout | 113 | 0.5075 | 0.5959 | 0.0883 | 1.894 | 9.0 |
| adx_ema_pullback | 98 | 0.2412 | 0.2970 | 0.0557 | 1.441 | 10.1 |
