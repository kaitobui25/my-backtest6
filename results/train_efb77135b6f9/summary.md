# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **6,048**
- Configs meeting non-expectancy gates: **10**
- Configs passing full selection: **10**
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
- Config ID: `38deef2b84bb44c4a7811326`
- Trades: `307`
- Expectancy: `0.265038R`
- Gross expectancy: `0.376475R`
- Average cost: `0.111437R`
- Profit factor: `1.423147`
- Max drawdown: `14.896654R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `b53285205dde1f61270aa13e`
- Trades: `59`
- Expectancy: `0.755401R`
- Gross expectancy: `0.836057R`
- Average cost: `0.080657R`
- Profit factor: `2.262563`
- Max drawdown: `9.792297R`

**REJECTED: insufficient sample (`59` < `300` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 307 | 0.2650 | 0.3765 | 0.1114 | 1.423 | 14.9 |
