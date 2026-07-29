# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `665743d2c92cb17b3336aaff83bc589ee91267a6be47552cbe824ffb4d0e0bbc`
- Exact configs evaluated: **242**
- Configs meeting non-expectancy gates: **35**
- Configs passing full selection: **34**
- Eligible near threshold: **1**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `266a196fd83701e24ccb656a`
- Trades: `72`
- Expectancy: `0.340559R`
- Gross expectancy: `0.428318R`
- Average cost: `0.087760R`
- Profit factor: `1.506613`
- Max drawdown: `8.904028R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `266a196fd83701e24ccb656a`
- Trades: `72`
- Expectancy: `0.340559R`
- Gross expectancy: `0.428318R`
- Average cost: `0.087760R`
- Profit factor: `1.506613`
- Max drawdown: `8.904028R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 72 | 0.3406 | 0.4283 | 0.0878 | 1.507 | 8.9 |
