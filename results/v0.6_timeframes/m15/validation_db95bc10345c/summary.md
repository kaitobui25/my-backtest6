# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `308b94395ac152fb9a99956479ae020ac54f24fc08e89a474811ab7492197e86`
- Exact configs evaluated: **20**
- Configs meeting non-expectancy gates: **9**
- Configs passing full selection: **9**
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
- Config ID: `6fff69e01e2c7aecac4926b6`
- Trades: `154`
- Expectancy: `0.284041R`
- Gross expectancy: `0.392397R`
- Average cost: `0.108357R`
- Profit factor: `1.406139`
- Max drawdown: `11.403397R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `6fff69e01e2c7aecac4926b6`
- Trades: `154`
- Expectancy: `0.284041R`
- Gross expectancy: `0.392397R`
- Average cost: `0.108357R`
- Profit factor: `1.406139`
- Max drawdown: `11.403397R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 154 | 0.2840 | 0.3924 | 0.1084 | 1.406 | 11.4 |
