# Adding or removing a strategy

## Disable or remove

Set `enabled: false` in `config/search.yaml`, or delete that strategy block.
No execution code needs to change.

Before running a large grid, count combinations:

```bat
count_configs.bat
```

## Add a simple indicator strategy

For a close-confirmed strategy that only needs long/short signals, use the
shared `PrecomputedSignalPlugin`. It automatically:

- deduplicates identical signal parameter combinations;
- caches indicators;
- stores signals as compact `int8` arrays;
- applies configurable ATR stop distance;
- sends signals into the one exact execution kernel.

Example:

```python
"""Example close/EMA signal strategy."""

from exactbt.indicators import IndicatorCache
from exactbt.strategies.signal_common import crossed_above, crossed_below
from exactbt.strategies.signal_plugin import PrecomputedSignalPlugin


def close_ema_cross(cache: IndicatorCache, p: dict):
    ema = cache.ema(int(p["ema_window"]))
    return crossed_above(cache.close, ema), crossed_below(cache.close, ema)


PLUGIN = PrecomputedSignalPlugin(
    name="close_ema_cross",
    signal_builder=close_ema_cross,
)
```

Add to YAML:

```yaml
- plugin: exactbt.strategies.my_strategy:PLUGIN
  enabled: true
  parameters:
    <<: *simple_execution
    ema_window: [20, 50, 100, 200]
```

The shared adapter recognizes these execution keys:

```text
atr_stop_window
atr_stop_multiplier
risk_reward
max_hold_bars
side: both | long | short
```

They are excluded from signal-cache keys, so changing RR does not recalculate
EMA/RSI/Bollinger signals.

## Add a stateful strategy

A setup such as liquidity sweep/reclaim needs candle-by-candle mutable state.
Create one module under `src/exactbt/strategies/` and export `PLUGIN` with:

1. `expand_grid()` — deterministic parameter combinations.
2. `prepare_features()` — cached indicator arrays.
3. `encode_parameters()` — compact NumPy parameter rows.
4. `reset_state_nb()` — initialize setup state.
5. `step_nb()` — inspect one eligible flat candle and optionally return:
   `(side, stop_value, stop_mode, setup_start_index)`.

Copy `liquidity_sweep.py` for a stateful example.

## Correctness rules

- `step_nb()` is called only when the whole candle was flat.
- Never read data after index `i`.
- Shift rolling breakout levels by one candle when current high/low is part of
  the rolling calculation.
- Do not implement exits inside a strategy plugin unless the common engine is
  intentionally extended and regression-tested for every strategy.
- Add a synthetic unit test for every new edge case.
- Bump the plugin version when signal semantics change so checkpoints and config
  IDs cannot silently reuse old results.
