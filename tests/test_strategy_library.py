"""Smoke and caching tests for every strategy enabled in the default YAML."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from conftest import make_candles
from exactbt.strategy_loader import load_strategy_plugin


def _library_candles(count: int = 420):
    x = np.arange(count, dtype=np.float64)
    # Trend + cycles + deterministic bursts create non-flat indicators and
    # enough warm-up for 200-candle windows without random test instability.
    close = 100.0 + 0.025 * x + 3.0 * np.sin(x / 11.0) + 1.2 * np.sin(x / 3.7)
    open_ = close + 0.15 * np.sin(x / 2.3)
    high = np.maximum(open_, close) + 0.7 + 0.15 * np.sin(x / 5.0) ** 2
    low = np.minimum(open_, close) - 0.7 - 0.15 * np.cos(x / 5.0) ** 2
    candles = make_candles(open_.tolist(), high.tolist(), low.tolist(), close.tolist())
    candles.frame["volume"] = 100.0 + (x % 17.0) * 8.0
    object.__setattr__(candles, "volume", np.ascontiguousarray(candles.frame["volume"].to_numpy(np.float64)))
    return candles


def test_every_default_strategy_loads_prepares_encodes_and_steps():
    project_root = Path(__file__).resolve().parents[1]
    raw = yaml.safe_load((project_root / "config" / "search.yaml").read_text(encoding="utf-8"))
    candles = _library_candles()
    names: set[str] = set()

    enabled_entries = [entry for entry in raw["strategies"] if entry.get("enabled", True)]
    assert len(enabled_entries) == 17

    for entry in enabled_entries:
        plugin = load_strategy_plugin(entry["plugin"])
        assert plugin.name not in names
        names.add(plugin.name)

        configs = plugin.expand_grid(entry["parameters"])
        assert configs, plugin.name
        config = configs[0]
        features = plugin.prepare_features(candles, [config])
        encoded = plugin.encode_parameters([config], features)
        assert encoded.float_params.shape[0] == 1
        assert encoded.int_params.shape[0] == 1
        assert features.float_features.shape[1] == len(candles.open)
        assert features.int_features.shape[1] == len(candles.open)

        state_f = np.empty(plugin.state_float_size, dtype=np.float64)
        state_i = np.empty(plugin.state_int_size, dtype=np.int64)
        plugin.reset_state_nb(state_i, state_f)
        result = plugin.step_nb(
            len(candles.open) - 1,
            candles.open,
            candles.high,
            candles.low,
            candles.close,
            candles.volume,
            candles.day_id,
            features.float_features,
            features.int_features,
            encoded.float_params[0],
            encoded.int_params[0],
            state_f,
            state_i,
        )
        assert len(result) == 4, plugin.name


def test_simple_signal_cache_ignores_rr_and_stop_multiplier():
    plugin = load_strategy_plugin(
        "exactbt.strategies.mean_reversion:BOLLINGER_REENTRY_PLUGIN"
    )
    candles = _library_candles()
    base = {
        "window": 20,
        "std_mult": 2.0,
        "regime_ema": 100,
        "atr_stop_window": 14,
        "side": "both",
        "max_hold_bars": 0,
    }
    configs = [
        {**base, "atr_stop_multiplier": 1.0, "risk_reward": 1.5},
        {**base, "atr_stop_multiplier": 2.0, "risk_reward": 3.0},
    ]
    features = plugin.prepare_features(candles, configs)

    # One unique signal definition produces only long + short rows. RR and stop
    # multiplier change execution, not signal calculation.
    assert features.int_features.shape[0] == 2
    assert features.float_features.shape[0] == 1
