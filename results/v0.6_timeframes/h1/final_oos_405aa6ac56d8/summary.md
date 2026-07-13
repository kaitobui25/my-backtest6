# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **237**
- Configs meeting non-expectancy gates: **65**
- Configs passing full selection: **64**
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
- Config ID: `aa085378c7204645c1796f10`
- Trades: `21`
- Expectancy: `0.811774R`
- Gross expectancy: `0.883333R`
- Average cost: `0.071559R`
- Profit factor: `2.328257`
- Max drawdown: `5.368258R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `aa085378c7204645c1796f10`
- Trades: `21`
- Expectancy: `0.811774R`
- Gross expectancy: `0.883333R`
- Average cost: `0.071559R`
- Profit factor: `2.328257`
- Max drawdown: `5.368258R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 21 | 0.8118 | 0.8833 | 0.0716 | 2.328 | 5.4 |
| donchian_ema_atr | 22 | 0.1977 | 0.2802 | 0.0824 | 1.290 | 9.1 |
| squeeze_breakout | 32 | 0.1650 | 0.2539 | 0.0888 | 1.222 | 13.3 |
| donchian_breakout | 64 | 0.1148 | 0.1723 | 0.0575 | 1.185 | 10.7 |
