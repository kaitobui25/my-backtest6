# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **4,902**
- Configs meeting non-expectancy gates: **1,461**
- Configs passing full selection: **1,461**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `adx_ema_pullback`
- Config ID: `a7863125c1e710ce2066289d`
- Trades: `26`
- Expectancy: `0.599019R`
- Gross expectancy: `0.661414R`
- Average cost: `0.062395R`
- Profit factor: `2.294189`
- Max drawdown: `4.776262R`

## Best raw result — diagnostic only

- Strategy: `adx_ema_pullback`
- Config ID: `a7863125c1e710ce2066289d`
- Trades: `26`
- Expectancy: `0.599019R`
- Gross expectancy: `0.661414R`
- Average cost: `0.062395R`
- Profit factor: `2.294189`
- Max drawdown: `4.776262R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| adx_ema_pullback | 26 | 0.5990 | 0.6614 | 0.0624 | 2.294 | 4.8 |
| rolling_range_breakout | 37 | 0.4224 | 0.5135 | 0.0911 | 1.625 | 6.9 |
