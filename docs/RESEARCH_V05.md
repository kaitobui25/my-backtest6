# ExactBT v0.5 — Momentum and Trend-Continuation Research

## Goal

Re-test the momentum and trend-continuation families from v0.2 with execution
parameters that allow trends to develop: wider ATR stops, larger fixed-R targets,
longer holding periods, and explicit long/short separation.

The exact execution kernel remains unchanged. Signals are still confirmed on the
close and entered at the next candle open.

## Scope

Included families:

| Family | Exact configs | Hypothesis |
|---|---:|---|
| RSI momentum | 1,458 | RSI crosses a momentum threshold in the EMA regime |
| ROC momentum | 2,592 | Percentage rate of change crosses a directional threshold |
| MACD momentum | 1,944 | MACD cross agrees with histogram and EMA regime |
| EMA crossover | 648 | Fast EMA crosses slow EMA |
| EMA-slope pullback | 4,374 | Price resumes a sloping EMA trend after an ATR pullback |
| **Total** | **11,016** | |

Breakout, volatility-expansion, squeeze, and volume-confirmed families are not
included. They should be researched separately because their range, contraction,
and volume parameters form a different search problem.

## What changed from v0.2

The signal definitions remain unchanged. The execution grid becomes:

```text
ATR stop multiplier: 2.0, 3.0, 4.0
Risk/reward:         2.0, 3.0, 4.0
Maximum hold:        96, 192, 384 bars
Direction:           both, long-only, short-only
```

On 15-minute data, these hold limits are 1, 2, and 4 days. This is intentional:
momentum systems can be damaged by forcing every trade to finish within a few
hours.

The grid is still bounded. It does not blindly extend every parameter because a
larger Cartesian search increases multiple-testing risk and makes isolated TRAIN
winners easier to manufacture.

## Run TRAIN

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.5_momentum_trend.yaml `
  --split train
```

Analyze the latest result:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_results.py
```

## Decision rules

TRAIN uses the same hard predeclared gate as v0.3 and v0.4:

```text
Net expectancy > 0.15R
Trades >= 300
Profit factor >= 1.30
Cost share of gross wins <= 40%
```

Do not lower the gate after viewing the run. A configuration below the hard gate
may be tagged as a research lead, but it is not a passing strategy.

For each family inspect:

- whether positive results exist across a neighborhood;
- whether the edge is long-only, short-only, or both;
- whether wider stops reduce cost in R without destroying PF;
- whether longer hold limits improve results consistently;
- whether the optimum is pinned to RR, stop, or hold boundaries;
- yearly and regime stability.

## Boundary follow-up

A boundary extension is justified only when a family shows coherent evidence,
for example several neighboring configurations improve toward the largest tested
hold or stop value. Create a new focused YAML for that family rather than adding
more values to all five families at once.

Example:

```text
v0.5 result shows EMA-slope pullback improving at 4 ATR and 384 bars
→ create v0.5b for that family only
→ extend one or two boundaries
→ keep the original v0.5 result unchanged
```

## Freeze before VALIDATION

```powershell
.\.venv\Scripts\python.exe scripts\freeze_shortlist.py `
  results\<train_run_id> `
  --output config\shortlists\research_v05_train.json
```

Copy the TRAIN config, set:

```yaml
search:
  shortlist_file: config/shortlists/research_v05_train.json
```

and run:

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.5_validation.yaml `
  --split validation
```

Validation requires positive net expectancy, at least 80 trades, and PF at least
1.15. Do not edit those gates after seeing validation results.

## Interpretation

A failed v0.5 rejects these exact signal definitions and execution combinations.
It does not prove that every momentum or trend strategy is impossible.

A clean failure should lead to a structural hypothesis such as pullback/retest,
multi-timeframe context, or a different exit model. It should not lead to endless
micro-adjustment of indicator periods on the same TRAIN sample.
