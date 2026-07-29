# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **11,251**
- Configs meeting non-expectancy gates: **2,598**
- Configs passing full selection: **2,598**
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
- Config ID: `99399684465bc5bb61fbc558`
- Trades: `20`
- Expectancy: `0.791537R`
- Gross expectancy: `0.832239R`
- Average cost: `0.040702R`
- Profit factor: `3.368332`
- Max drawdown: `3.385919R`

## Best raw result — diagnostic only

- Strategy: `adx_ema_pullback`
- Config ID: `99399684465bc5bb61fbc558`
- Trades: `20`
- Expectancy: `0.791537R`
- Gross expectancy: `0.832239R`
- Average cost: `0.040702R`
- Profit factor: `3.368332`
- Max drawdown: `3.385919R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| adx_ema_pullback | 20 | 0.7915 | 0.8322 | 0.0407 | 3.368 | 3.4 |
| rolling_range_breakout | 17 | 0.6621 | 0.7050 | 0.0429 | 2.188 | 2.2 |
