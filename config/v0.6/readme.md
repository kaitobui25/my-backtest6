# ExactBT v0.6 timeframe configs

This folder contains controlled BTC timeframe comparisons for:

- M5
- M15
- M30
- H1
- H2
- H4

Every YAML keeps the same v0.6 strategies, parameter grid, fees, slippage, data splits, and sample-size gates. Only the Parquet file/timeframe changes.

Selection gates on every split:

```yaml
min_expectancy_r: 0.1
min_profit_factor: 1.15
```

TRAIN keeps `min_trades: 300`; VALIDATION and FINAL OOS keep `min_trades: 80`. These gates are not reduced for slower timeframes merely to manufacture passing results.

H6, H8, H12, D1, D3, W1, and MN1 are intentionally excluded from this v0.6 comparison. With the current 2021-01-01 to 2024-07-01 TRAIN split and breakout grid, they are unlikely to provide the required 300 trades. They need a separate low-frequency research design and sample-size policy rather than copied v0.6 YAML.

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
