# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **364**
- Configs meeting non-expectancy gates: **116**
- Configs passing full selection: **115**
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
- Config ID: `cce2d587d6373012abf435a9`
- Trades: `19`
- Expectancy: `1.147222R`
- Gross expectancy: `1.196482R`
- Average cost: `0.049260R`
- Profit factor: `3.302800`
- Max drawdown: `6.329183R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `cce2d587d6373012abf435a9`
- Trades: `19`
- Expectancy: `1.147222R`
- Gross expectancy: `1.196482R`
- Average cost: `0.049260R`
- Profit factor: `3.302800`
- Max drawdown: `6.329183R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 19 | 1.1472 | 1.1965 | 0.0493 | 3.303 | 6.3 |
| squeeze_breakout | 21 | 0.5418 | 0.5865 | 0.0448 | 2.102 | 3.1 |
| donchian_ema_atr | 37 | 0.2555 | 0.3093 | 0.0539 | 1.332 | 10.4 |
