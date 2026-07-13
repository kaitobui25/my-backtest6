# ExactBT Search Summary

- Split: `validation`
- Dataset SHA-256: `6d08f2caa11c2e68676e510561a51726848f8fe33400f567478fe352deafa5ea`
- Exact configs evaluated: **408**
- Configs meeting non-expectancy gates: **212**
- Configs passing full selection: **212**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

- Strategy: `donchian_ema_atr`
- Config ID: `2bd4113318bb9e2fced5a461`
- Trades: `10`
- Expectancy: `1.011859R`
- Gross expectancy: `1.041889R`
- Average cost: `0.030030R`
- Profit factor: `2.967307`
- Max drawdown: `3.086408R`

## Best raw result — diagnostic only

- Strategy: `donchian_ema_atr`
- Config ID: `9ae2ceade83a931a22d65956`
- Trades: `9`
- Expectancy: `1.439513R`
- Gross expectancy: `1.475941R`
- Average cost: `0.036428R`
- Profit factor: `4.127690`
- Max drawdown: `2.074394R`

**REJECTED: insufficient sample (`9` < `10` trades).**

## Best eligible by strategy

| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |
|---|---:|---:|---:|---:|---:|---:|
| donchian_ema_atr | 10 | 1.0119 | 1.0419 | 0.0300 | 2.967 | 3.1 |
| donchian_breakout | 10 | 0.9944 | 1.0250 | 0.0306 | 2.931 | 3.1 |
| atr_expansion_breakout | 11 | 0.9851 | 1.0126 | 0.0275 | 3.110 | 2.1 |
| squeeze_breakout | 11 | 0.3272 | 0.3636 | 0.0364 | 1.579 | 2.1 |
