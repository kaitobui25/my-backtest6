# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `1eec0c9090b7dbc3de8c5fb0e4bd1c7b67c4cc8ddb610599095b902fbd6e7502`
- Exact configs evaluated: **684**
- Configs meeting non-expectancy gates: **240**
- Configs passing full selection: **237**
- Eligible near threshold: **3**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `64f51e7886a0644a2a957aa7`
- Trades: `21`
- Expectancy: `0.630963R`
- Gross expectancy: `0.669343R`
- Average cost: `0.038380R`
- Profit factor: `2.023683`
- Max drawdown: `4.662931R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `64f51e7886a0644a2a957aa7`
- Trades: `21`
- Expectancy: `0.630963R`
- Gross expectancy: `0.669343R`
- Average cost: `0.038380R`
- Profit factor: `2.023683`
- Max drawdown: `4.662931R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 21 | 0.6310 | 0.6693 | 0.0384 | 2.024 | 4.7 |
| squeeze_breakout | 34 | 0.3902 | 0.4706 | 0.0804 | 1.509 | 7.6 |
| donchian_ema_atr | 38 | 0.3250 | 0.3956 | 0.0706 | 1.627 | 6.4 |
| donchian_breakout | 37 | 0.3209 | 0.3913 | 0.0703 | 1.637 | 6.4 |
