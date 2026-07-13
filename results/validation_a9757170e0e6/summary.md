# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **10**
- Configs meeting non-expectancy gates: **5**
- Configs passing full selection: **5**
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
- Config ID: `822ac1aad189d96be19dd215`
- Trades: `96`
- Expectancy: `0.197941R`
- Gross expectancy: `0.282067R`
- Average cost: `0.084126R`
- Profit factor: `1.367546`
- Max drawdown: `11.668413R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `822ac1aad189d96be19dd215`
- Trades: `96`
- Expectancy: `0.197941R`
- Gross expectancy: `0.282067R`
- Average cost: `0.084126R`
- Profit factor: `1.367546`
- Max drawdown: `11.668413R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 96 | 0.1979 | 0.2821 | 0.0841 | 1.368 | 11.7 |
