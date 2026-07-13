# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **860**
- Configs meeting non-expectancy gates: **369**
- Configs passing full selection: **364**
- Eligible near threshold: **5**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `017d1ddf5ca23238e4afc212`
- Trades: `11`
- Expectancy: `1.352834R`
- Gross expectancy: `1.395311R`
- Average cost: `0.042477R`
- Profit factor: `4.352286`
- Max drawdown: `2.365297R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `017d1ddf5ca23238e4afc212`
- Trades: `11`
- Expectancy: `1.352834R`
- Gross expectancy: `1.395311R`
- Average cost: `0.042477R`
- Profit factor: `4.352286`
- Max drawdown: `2.365297R`

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 11 | 1.3528 | 1.3953 | 0.0425 | 4.352 | 2.4 |
| squeeze_breakout | 12 | 0.6774 | 0.7243 | 0.0469 | 2.105 | 2.2 |
| donchian_breakout | 17 | 0.6717 | 0.7107 | 0.0390 | 2.360 | 3.7 |
| donchian_ema_atr | 17 | 0.6717 | 0.7107 | 0.0390 | 2.360 | 3.7 |
