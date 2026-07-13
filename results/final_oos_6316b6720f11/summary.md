# ExactBT Search Summary

- Split: `final_oos`
- Dataset SHA-256: `0f50f4f74fa0efd86c92f27829379b5215750e7b5284d60e7fb7ce1784d0dcbc`
- Exact configs evaluated: **5**
- Configs meeting non-expectancy gates: **0**
- Configs passing full selection: **0**
- Eligible near threshold: **0**

## Expectancy rule

```text
gross_expectancy_R = gross_win_rate × avg_gross_win_R
                     - gross_loss_rate × avg_gross_loss_R
expectancy_R = gross_expectancy_R - avg_cost_R
source of truth = net_R_total / trades
```

## Best eligible result

No configuration met the non-expectancy gates, including `trades >= 80`.

## Best raw result — diagnostic only

- Strategy: `atr_expansion_breakout`
- Config ID: `9b7e4f557c897b47e2f7dc05`
- Trades: `110`
- Expectancy: `-0.072800R`
- Gross expectancy: `0.022268R`
- Average cost: `0.095068R`
- Profit factor: `0.892852`
- Max drawdown: `28.047562R`

## Best eligible by strategy

No strategy has a sample-eligible configuration.
