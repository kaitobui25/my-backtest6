# ExactBT v0.3 focused research

## Why v0.2 found no candidate

The v0.2 run is useful evidence, not a failed program:

- all 23,796 declared configurations completed on TRAIN;
- zero configurations passed `expectancy_R > 0.15` with at least 300 trades;
- the reported raw winner had one trade and was not a valid candidate;
- most converted indicator families shared the same ATR stop, fixed-RR target and
  very coarse hold-time grid.

That search therefore falsified the tested combinations. It did **not** prove
that every strategy carrying the same indicator name is unprofitable.

## What changes in v0.3

The exact execution kernel is unchanged. Research changes are isolated to:

1. reporting that separates raw winners from sample-eligible winners;
2. near-threshold filtering that also enforces minimum trades and risk gates;
3. a frozen TRAIN shortlist for VALIDATION;
4. a focused grid of structurally different entries and family-specific exits.

The focused config contains 10,224 exact combinations:

| Family | Configs | Main hypothesis |
|---|---:|---|
| ADX + EMA pullback | 1,152 | Continue a strong trend after a confirmed pullback |
| Daily VWAP reclaim | 1,728 | Intraday location plus trend and relative volume |
| Rolling sweep/reclaim | 3,456 | Failed breakout with stop beyond the actual wick |
| Rolling-range breakout | 3,888 | Existing breakout with wider stops, longer holds and side separation |

These are hypotheses. Nothing is called profitable until TRAIN and frozen
VALIDATION both support it.

## Run TRAIN

```bat
.venv\Scripts\python.exe -m exactbt.cli search ^
  --config config\search_v0.3_research.yaml ^
  --split train
```

Analyze the latest TRAIN run:

```bat
.venv\Scripts\python.exe scripts\analyze_results.py
```

The analyzer writes:

```text
results/<run_id>/diagnostics/
├── diagnostics.md
├── strategy_diagnostics.csv
├── parameter_sensitivity.csv
├── top_raw.csv
├── top_eligible.csv
├── passing.csv
└── near_threshold_eligible.csv
```

## Freeze before VALIDATION

Do not edit parameters after looking at VALIDATION. Freeze TRAIN candidates:

```bat
.venv\Scripts\python.exe scripts\freeze_shortlist.py ^
  results\<train_run_id> ^
  --output config\shortlists\research_v03_train.json
```

Then set in a copy of the research YAML:

```yaml
search:
  shortlist_file: config/shortlists/research_v03_train.json
```

Run only those frozen parameters:

```bat
.venv\Scripts\python.exe -m exactbt.cli search ^
  --config config\search_v0.3_validation.yaml ^
  --split validation
```

The workflow rejects a shortlist on TRAIN and records the shortlist SHA-256 in
the run manifest.

## Decision rule

A useful candidate should not merely clear one threshold. Inspect:

- net expectancy after costs;
- gross expectancy and average cost separately;
- at least 300 TRAIN trades;
- no dependence on one isolated parameter point;
- both time subperiods and long/short decomposition;
- frozen VALIDATION performance before any final OOS access.

If no sample-eligible family has positive net expectancy, do not lower the goal
only to manufacture a winner. The next research step should change information
or market structure, for example multi-timeframe context, session conditioning,
funding/open-interest data, or a different execution horizon.
