# ExactBT Search Summary

- Split: `train`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **23,796**
- Configs passing selection: **0**
- Near threshold: **18**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best exact result

- Strategy: `ema_slope_pullback`
- Config ID: `095be0aaecf999edd0aeb90c`
- Trades: `1`
- Expectancy: `2.291090R`
- Gross expectancy: `2.500000R`
- Average cost: `0.208910R`
- Profit factor: `inf`
- Max drawdown: `0.000000R`
