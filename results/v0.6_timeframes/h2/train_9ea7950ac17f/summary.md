# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `503cad72b8f65515c61de7b1612277584ca5e4e653e88cf25aa4c57b64a668e7`
- Exact configs evaluated: **6,048**
- Configs meeting non-expectancy gates: **874**
- Configs passing full selection: **860**
- Eligible near threshold: **14**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `atr_expansion_breakout`
- Config ID: `bd35a083cd03de30323064bd`
- Trades: `41`
- Expectancy: `0.695582R`
- Gross expectancy: `0.725284R`
- Average cost: `0.029702R`
- Profit factor: `2.300506`
- Max drawdown: `5.644295R`

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `61eefeb99fedc13ed504d152`
- Trades: `5`
- Expectancy: `1.964383R`
- Gross expectancy: `2.000000R`
- Average cost: `0.035617R`
- Profit factor: `5.728769`
- Max drawdown: `1.040831R`

**REJECTED: insufficient sample (`5` < `40` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| atr_expansion_breakout | 41 | 0.6956 | 0.7253 | 0.0297 | 2.301 | 5.6 |
| donchian_ema_atr | 85 | 0.6650 | 0.6983 | 0.0332 | 2.117 | 8.2 |
| squeeze_breakout | 50 | 0.5500 | 0.5835 | 0.0335 | 1.948 | 7.3 |
| donchian_breakout | 60 | 0.4407 | 0.4737 | 0.0329 | 1.675 | 10.3 |
