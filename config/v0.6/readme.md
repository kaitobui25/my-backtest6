# ExactBT v0.6 timeframe configs

This folder contains BTC v0.6 breakout/volatility TRAIN configs for:

- M5
- M15
- M30
- H1
- H2
- H4

All files keep the same strategies, parameter grid, fees, slippage, and date splits. The dataset, timeframe-specific sample gate, and result directory differ by file.

## Selection thresholds

Every split requires:

```yaml
min_expectancy_r: 0.1
strict_expectancy: true
min_profit_factor: 1.15
```

Because `strict_expectancy` is enabled, the expectancy condition is strictly greater than `0.10R`.

## Timeframe-specific `min_trades`

M15 is the reference: `300` TRAIN trades and `80` trades on each one-year VALIDATION/OOS split.

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

## One-click TRAIN runner

From Windows Explorer, double-click:

```text
run_v0.6_all_timeframes.bat
```

The BAT runs sequentially:

```text
M5 -> M15 -> M30 -> H1 -> H2 -> H4
```

It stops immediately if one timeframe fails. ExactBT checkpoints already written are preserved, so running the BAT again resumes completed batches.

The BAT intentionally runs TRAIN only. VALIDATION and FINAL OOS must use frozen passing shortlists from the preceding split; running the full parameter grid directly on those splits would invalidate the research workflow.

## Result layout

Each config writes to its own directory:

```text
results/
└── v0.6_timeframes/
    ├── m5/
    │   └── train_<hash>/
    ├── m15/
    │   └── train_<hash>/
    ├── m30/
    │   └── train_<hash>/
    ├── h1/
    │   └── train_<hash>/
    ├── h2/
    │   └── train_<hash>/
    ├── h4/
    │   └── train_<hash>/
    └── run_all_status.log
```

The status log records the start, completion, or failure of each timeframe. Full ExactBT metrics and checkpoints remain inside the corresponding `train_<hash>` folder.

## Why slower timeframes are not copied here

H6, H8, H12, D1, D3, W1, and MN1 need more than a smaller `min_trades`. The current v0.6 parameters are expressed in bars (`lookback` up to 384, EMA up to 200, and hold up to 384), so copying the grid unchanged to slow candles changes the real-time strategy horizon drastically and may leave too little usable history. Those timeframes require a separately scaled parameter grid.
