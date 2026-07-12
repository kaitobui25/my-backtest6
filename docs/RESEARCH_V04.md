# ExactBT v0.4 — Mean-Reversion Research

## Goal

Re-test the four mean-reversion families from the broad v0.2 scan without
changing the authoritative execution kernel.

The v0.2 result rejected the tested combinations. It did not prove that every
Bollinger, Z-score, or RSI mean-reversion design is unprofitable. The main v0.4
change is therefore an execution grid designed for shorter-lived reversion
trades rather than the coarse grid shared by many unrelated strategies in v0.2.

## Scope

Included families:

| Family | Exact configs | Hypothesis |
|---|---:|---|
| Bollinger re-entry | 1,944 | Price closes outside a band, then closes back inside it |
| Bollinger wick fade | 1,944 | Wick crosses a band while the close returns inside |
| Z-score reversion | 1,728 | Standardized price deviation crosses back toward the mean |
| RSI extreme recovery | 2,592 | RSI recovers from an overbought/oversold extreme |
| **Total** | **8,208** | |

Not included:

- custom mid-band exits;
- swing-structure stops;
- session filters;
- volatility-regime classifiers;
- scaling, partial exits, or trailing stops;
- new signal source code.

Those are separate hypotheses. Adding them before measuring this execution-only
redesign would make the result difficult to interpret.

## What changed from v0.2

The close-confirmed signal definitions remain unchanged. The experiment changes
only declared parameters:

```text
ATR stop multiplier: 1.0, 1.5, 2.0
Risk/reward:         0.75, 1.0, 1.25, 1.5
Maximum hold:        16, 32, 64 bars
Direction:           both, long-only, short-only
```

On 15-minute candles, the hold grid corresponds to 4, 8, and 16 hours. This is
intentionally shorter than the momentum/trend experiment.

The lower fixed-R targets are deliberate. A mean-reversion setup does not need
to be forced into the same 2R–4R target structure as a breakout or trend trade.

## Run TRAIN

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.4_mean_reversion.yaml `
  --split train
```

Analyze the latest result:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_results.py
```

## Decision rules

The hard TRAIN gate remains predeclared:

```text
Net expectancy > 0.15R
Trades >= 300
Profit factor >= 1.30
Cost share of gross wins <= 40%
```

Do not lower these values after seeing TRAIN merely to manufacture a passing
configuration. Near-threshold and family-best files are diagnostic evidence,
not proof of a tradable edge.

Inspect more than the top row:

- median and best expectancy for each family;
- long/short decomposition;
- cost in R;
- parameter neighborhoods, not one isolated optimum;
- performance by subperiod;
- whether the best point lies on a search boundary.

## Freeze before VALIDATION

Freeze only TRAIN candidates that satisfy the predeclared research rules:

```powershell
.\.venv\Scripts\python.exe scripts\freeze_shortlist.py `
  results\<train_run_id> `
  --output config\shortlists\research_v04_train.json
```

Copy the TRAIN YAML to a validation YAML and set:

```yaml
search:
  shortlist_file: config/shortlists/research_v04_train.json
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m exactbt.cli search `
  --config config\search_v0.4_validation.yaml `
  --split validation
```

The validation gate is already declared in the config: positive net expectancy,
at least 80 trades, and profit factor at least 1.15.

## Interpretation

A failed v0.4 means the current close-confirmed signal definitions plus this
short-horizon ATR/fixed-R execution grid did not produce a robust candidate. It
does not reject every possible mean-reversion strategy.

A sensible next step after a clean failure is to change information or exit
structure, for example volatility conditioning or a mean-target exit. It is not
to keep adding tiny parameter increments around the best TRAIN row indefinitely.
