# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `665743d2c92cb17b3336aaff83bc589ee91267a6be47552cbe824ffb4d0e0bbc`
- Exact configs evaluated: **6,048**
- Configs meeting non-expectancy gates: **249**
- Configs passing full selection: **242**
- Eligible near threshold: **7**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `205dc42ed9917dcc5ce60f33`
- Trades: `163`
- Expectancy: `0.402318R`
- Gross expectancy: `0.472484R`
- Average cost: `0.070166R`
- Profit factor: `1.645188`
- Max drawdown: `7.206276R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `e7962335d9c7d454c1ca2e2c`
- Trades: `38`
- Expectancy: `0.796217R`
- Gross expectancy: `0.872753R`
- Average cost: `0.076536R`
- Profit factor: `2.323465`
- Max drawdown: `6.513979R`

**REJECTED: insufficient sample (`38` < `150` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 163 | 0.4023 | 0.4725 | 0.0702 | 1.645 | 7.2 |
| donchian_ema_atr | 176 | 0.2814 | 0.3635 | 0.0821 | 1.390 | 14.0 |
| donchian_breakout | 173 | 0.2538 | 0.3367 | 0.0829 | 1.346 | 14.1 |
