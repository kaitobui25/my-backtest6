# ExactBT v0.6 — Breakout and Volatility Research

## Goal

Re-test the four breakout/volatility families that were still only covered by the
broad v0.2 execution grid. The exact kernel, next-open entry, SL/TP handling,
fees, slippage, both-hit rule, checkpointing, and reporting remain unchanged.

Rolling-range breakout is not repeated here because it was already investigated
in v0.3 with a dedicated grid.

## Scope

| Family | Exact configs | Hypothesis |
|---|---:|---|
| Donchian breakout | 288 | Close breaks a prior channel in an EMA regime |
| Donchian + EMA + ATR | 576 | Independent Donchian implementation with ATR stop |
| ATR-expansion breakout | 1,728 | Breakout occurs while ATR is elevated |
| Squeeze breakout | 3,456 | A recent low-bandwidth state precedes breakout |
| **Total** | **6,048** | |

## Execution grid

```text
ATR stop multiplier: 3.0, 4.0
Risk/reward:         2.0, 3.0, 4.0
Maximum hold:        192, 384 bars
Direction:           both, long-only, short-only
```

On 15-minute data the hold limits are two and four days. This is intentional:
breakout systems need enough room for price expansion, while the grid remains
bounded to avoid blindly multiplying TRAIN trials.

## Run TRAIN

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.6_breakout_volatility.yaml `
  --split train
```

Then analyze the generated run:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_results.py
```

## Decision rules

TRAIN keeps the predeclared hard gate:

```text
Net expectancy > 0.15R
Trades >= 300
Profit factor >= 1.30
Cost share of gross wins <= 40%
```

Inspect more than the top row. A useful lead should show a neighborhood across
lookback, stop, RR, hold, or volatility parameters. If the winner is pinned to a
boundary, create a new declared boundary experiment rather than editing this
config after seeing the result.

Freeze TRAIN candidates before running Validation. Final OOS remains locked.
