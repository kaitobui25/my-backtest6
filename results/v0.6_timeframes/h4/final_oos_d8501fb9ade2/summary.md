# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **212**
- Configs meeting non-expectancy gates: **19**
- Configs passing full selection: **17**
- Eligible near threshold: **2**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `5225598975575a7c5661a706`
- Trades: `14`
- Expectancy: `0.871877R`
- Gross expectancy: `0.906600R`
- Average cost: `0.034723R`
- Profit factor: `2.958893`
- Max drawdown: `4.165266R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `5225598975575a7c5661a706`
- Trades: `14`
- Expectancy: `0.871877R`
- Gross expectancy: `0.906600R`
- Average cost: `0.034723R`
- Profit factor: `2.958893`
- Max drawdown: `4.165266R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 14 | 0.8719 | 0.9066 | 0.0347 | 2.959 | 4.2 |
| donchian_ema_atr | 20 | 0.4876 | 0.5168 | 0.0293 | 2.146 | 3.5 |
| donchian_breakout | 11 | 0.3173 | 0.3636 | 0.0463 | 1.558 | 2.2 |
