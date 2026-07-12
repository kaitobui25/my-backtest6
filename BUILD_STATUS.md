# Build status — v0.2.0

Validated on 2026-07-12 with Python 3.13.5 in the build environment.
The package declares Python 3.11–3.13 support.

## Strategy integration

The five supplied strategy files were converted from their original `btsearch`
interfaces into ExactBT plugins:

- 4 mean-reversion strategies;
- 3 momentum strategies;
- 4 trend/breakout strategies;
- 2 volatility strategies;
- 2 volume-confirmed strategies.

Together with the two existing plugins, the default YAML enables **17 strategy
families** and expands to **23,796 exact configurations**.

The uploaded strategies originally returned entry signals only. The converted
plugins therefore use one explicit, configurable ATR-distance stop model through
the shared `simple_strategy_execution` YAML anchor. No strategy received a
private copy of entry/exit, fee, slippage, or trade-record logic.

## Automated tests

```text
10 passed
```

Covered invariants:

- next-candle-open entry and entry-bar SL/TP;
- conservative stop priority when SL and TP both hit;
- stop gaps fill at candle open;
- no same-candle re-entry after an exit;
- a pending entry cancelled on a new day does not hide that new candle;
- expectancy after fees/slippage;
- batch-metrics and record-mode parity;
- deterministic Cartesian grid and dynamic plugin loading;
- Liquidity Sweep same-candle sweep/reclaim state;
- all 17 default plugins load, prepare features, encode parameters and execute
  their strategy step;
- signal cache reuses one signal definition across different RR and ATR-stop
  multiplier combinations.

## Required real-data gate

The indicator definitions and integration are code-tested, but results are not
yet regression-validated against the user's real BTC Parquet or the old
`btsearch` framework. Before treating performance as trustworthy:

1. run TRAIN on the real Parquet;
2. inspect strategy trade records;
3. compare selected known configurations with the old implementation;
4. lock those results as regression fixtures;
5. only then run VALIDATION and final locked OOS.
