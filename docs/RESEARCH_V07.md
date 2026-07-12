# ExactBT v0.7 — Volume-Confirmed Research

## Goal

Re-test the two volume-confirmed families from v0.2 with explicit long/short
separation and execution parameters suitable for momentum continuation. The
signal definitions still use current volume versus a rolling volume mean, and
entry remains the next candle open.

## Scope

| Family | Exact configs | Hypothesis |
|---|---:|---|
| Breakout + volume | 1,296 | Rolling breakout is confirmed by relative volume |
| ROC momentum + volume | 5,184 | Momentum threshold cross is confirmed by relative volume |
| **Total** | **6,480** | |

## Execution grid

```text
ATR stop multiplier: 2.0, 3.0
Risk/reward:         2.0, 3.0, 4.0
Maximum hold:        96, 192, 384 bars
Direction:           long-only, short-only
```

`both` is deliberately omitted. The experiment measures each direction directly
and avoids creating a second combined-direction copy of the same parameter set.

The relative-volume grid remains limited to rolling windows 20/50/100 and
multipliers 1.2/1.5/2.0. If all results fail, that rejects these implementations;
it does not prove that order flow or every possible volume model has no edge.

## Run TRAIN

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.7_volume_confirmed.yaml `
  --split train
```

Analyze:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_results.py
```

## Decision rules

```text
Net expectancy > 0.15R
Trades >= 300
Profit factor >= 1.30
Cost share of gross wins <= 40%
```

Review whether volume confirmation improves net expectancy after cost, whether
one direction dominates, and whether a positive result persists across nearby
volume windows and multipliers. Freeze TRAIN candidates before Validation.
