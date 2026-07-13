# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **6,480**
- Configs meeting non-expectancy gates: **8**
- Configs passing full selection: **8**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `momentum_volume`
- Config ID: `8d7aae58e2a85403e23910e0`
- Trades: `326`
- Expectancy: `0.250062R`
- Gross expectancy: `0.362390R`
- Average cost: `0.112328R`
- Profit factor: `1.355611`
- Max drawdown: `18.246877R`

## Best raw result — diagnostic only

- Strategy: `momentum_volume`
- Config ID: `558f5f55fcef2999a8507947`
- Trades: `280`
- Expectancy: `0.284105R`
- Gross expectancy: `0.400892R`
- Average cost: `0.116787R`
- Profit factor: `1.405466`
- Max drawdown: `13.084254R`

**REJECTED: insufficient sample (`280` < `300` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| momentum_volume | 326 | 0.2501 | 0.3624 | 0.1123 | 1.356 | 18.2 |
