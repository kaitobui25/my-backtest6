# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `665743d2c92cb17b3336aaff83bc589ee91267a6be47552cbe824ffb4d0e0bbc`
- Exact configs evaluated: **34**
- Configs meeting non-expectancy gates: **1**
- Configs passing full selection: **1**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `534443de149ca9926988e67b`
- Trades: `52`
- Expectancy: `0.223150R`
- Gross expectancy: `0.299987R`
- Average cost: `0.076837R`
- Profit factor: `1.327086`
- Max drawdown: `12.203513R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `534443de149ca9926988e67b`
- Trades: `52`
- Expectancy: `0.223150R`
- Gross expectancy: `0.299987R`
- Average cost: `0.076837R`
- Profit factor: `1.327086`
- Max drawdown: `12.203513R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 52 | 0.2231 | 0.3000 | 0.0768 | 1.327 | 12.2 |
