# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **6,048**
- Configs meeting non-expectancy gates: **412**
- Configs passing full selection: **408**
- Eligible near threshold: **4**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `e875de63bd5e4df9fc35ac61`
- Trades: `31`
- Expectancy: `1.205220R`
- Gross expectancy: `1.234135R`
- Average cost: `0.028916R`
- Profit factor: `3.596029`
- Max drawdown: `3.082712R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `d08ea55b1cb0e58a8ee35894`
- Trades: `2`
- Expectancy: `3.623909R`
- Gross expectancy: `3.653045R`
- Average cost: `0.029136R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`

**REJECTED: insufficient sample (`2` < `30` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 31 | 1.2052 | 1.2341 | 0.0289 | 3.596 | 3.1 |
| donchian_ema_atr | 37 | 0.6372 | 0.6609 | 0.0237 | 2.325 | 6.4 |
| donchian_breakout | 36 | 0.6218 | 0.6457 | 0.0238 | 2.128 | 4.4 |
| squeeze_breakout | 31 | 0.2278 | 0.2581 | 0.0303 | 1.382 | 4.1 |
