# ExactBT v0.6 timeframe configs

This folder contains controlled BTC timeframe comparisons for:

- M5
- M15
- M30
- H1
- H2
- H4

Every YAML keeps the same v0.6 strategies, parameter grid, fees, slippage, and data splits. Only the Parquet dataset/timeframe and the sample-size gate change.

Selection thresholds on every split:

```yaml
min_expectancy_r: 0.1
min_profit_factor: 1.15
```

## Timeframe-specific `min_trades`

M15 is the reference: `300` TRAIN trades and `80` trades on each one-year VALIDATION/OOS split.

For another timeframe, the gate is scaled inversely by candle duration:

```text
train_min = 300 × 15 minutes / timeframe_minutes
later_min = 80 × 15 minutes / timeframe_minutes
```

Rounded to practical integers, with floors of `30` TRAIN trades and `10` VALIDATION/OOS trades:

| Timeframe | TRAIN | VALIDATION | FINAL OOS |
|---|---:|---:|---:|
| M5 | 900 | 240 | 240 |
| M15 | 300 | 80 | 80 |
| M30 | 150 | 40 | 40 |
| H1 | 75 | 20 | 20 |
| H2 | 40 | 10 | 10 |
| H4 | 30 | 10 | 10 |

This keeps the required trade density comparable across candle sizes without lowering the gate arbitrarily just to create passing configs.

H6, H8, H12, D1, D3, W1, and MN1 are not included in this copied v0.6 grid. The current parameters are expressed in bars (`lookback` up to 384, EMA up to 200, and hold up to 384), so copying them unchanged to very slow candles changes the strategy horizon drastically and can leave too little usable history. Those timeframes need separately scaled parameter windows, not merely a smaller `min_trades` value.

Because these files are inside `config/v0.6/`, their project paths intentionally use `../data/...` and `../results` to match ExactBT's current relative-path resolver.

Run one TRAIN search from the repository root:

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config/v0.6/search_v0.6_breakout_volatility_m15.yaml `
  --split train
```

Run all six TRAIN searches sequentially:

```powershell
Get-ChildItem .\config\v0.6\search_v0.6_breakout_volatility_*.yaml |
  Sort-Object Name |
  ForEach-Object {
    & .\.venv\Scripts\python.exe -m exactbt.cli search `
      --config $_.FullName `
      --split train
    if ($LASTEXITCODE -ne 0) {
      throw "ExactBT failed for $($_.FullName)"
    }
  }
```
