# ExactBT v0.8 — PDH/PDL Liquidity Sweep Research

## Goal

Re-test the original stateful PDH/PDL liquidity-sweep family from v0.2 with a
bounded grid, explicit direction control, finite hold times, and the same exact
execution engine used by every other research round.

The setup remains:

```text
Sweep PDL -> reclaim above PDL -> LONG
Sweep PDH -> reclaim below PDH -> SHORT
Entry at next candle open
Stop outside the actual sweep extreme
```

## Scope

| Family | Exact configs |
|---|---:|
| PDH/PDL sweep + reclaim | 4,860 |

Parameters cover:

```text
Sweep buffer:       0, 0.025%, 0.05%
Reclaim buffer:     0, 0.025%, 0.05%
Maximum wait:       1, 2, 4, 8 candles
Stop buffer:        0, 0.01%, 0.02%
Risk/reward:        1.0, 1.5, 2.0, 2.5, 3.0
Maximum hold:       16, 32, 64 candles
Direction:          both, long-only, short-only
```

`max_wait_candles=1` covers same-candle sweep/reclaim. Larger values allow a
reclaim on later candles while retaining the most extreme wick for the stop.

## Source change

The liquidity plugin now supports optional `side` encoding:

```text
both  = 0
long  = 1
short = -1
```

Omitting `side` remains backward compatible and behaves as `both`. A candle that
sweeps both PDH and PDL is still rejected conservatively, even in a direction-
restricted run.

## Time model

This experiment uses previous UTC trading-day high/low only. It does not claim to
test Asia, London, or New York highs/lows. Session levels need explicit timezone,
DST, session boundaries, and level-availability rules, so they belong in a later
separately declared experiment.

## Run TRAIN

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.8_pdh_pdl_liquidity.yaml `
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

Pay special attention to sample size. A high-expectancy sweep configuration with
20-30 trades is a research lead, not a passing strategy. Freeze any declared
TRAIN shortlist before Validation; Final OOS remains locked.

## Coverage after v0.8

The original 17 broad-scan families are no longer abandoned:

- v0.4 re-tests four mean-reversion families;
- v0.5 re-tests five momentum/trend families;
- v0.6 re-tests four breakout/volatility families;
- v0.7 re-tests two volume-confirmed families;
- v0.8 re-tests the original liquidity-sweep family;
- rolling-range breakout was already covered deeply in v0.3.
