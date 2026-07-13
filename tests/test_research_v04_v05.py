"""Configuration and plugin checks for the v0.4/v0.5 research rounds."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from conftest import make_candles
from exactbt.strategy_loader import load_strategy_plugin


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(filename: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / "config" / filename).read_text(encoding="utf-8"))


def _grid_counts(raw: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in raw["strategies"]:
        plugin = load_strategy_plugin(entry["plugin"])
        assert plugin.name not in counts
        counts[plugin.name] = len(plugin.expand_grid(entry["parameters"]))
    return counts


def _research_candles(count: int = 520):
    x = np.arange(count, dtype=np.float64)
    close = 100.0 + 0.025 * x + 3.0 * np.sin(x / 11.0) + 0.8 * np.sin(x / 3.0)
    open_ = close - 0.25 * np.sin(x / 4.0)
    high = np.maximum(open_, close) + 0.9 + 0.1 * np.sin(x / 7.0)
    low = np.minimum(open_, close) - 0.9 - 0.1 * np.cos(x / 7.0)
    candles = make_candles(open_.tolist(), high.tolist(), low.tolist(), close.tolist())
    volume = 100.0 + (x % 17.0) * 9.0
    candles.frame["volume"] = volume
    object.__setattr__(candles, "volume", np.ascontiguousarray(volume))
    return candles


def test_v04_mean_reversion_grid_count_and_plugins_load():
    raw = _load_yaml("search_v0.4_mean_reversion.yaml")
    counts = _grid_counts(raw)

    assert counts == {
        "bollinger_reentry": 1944,
        "bollinger_fade": 1944,
        "zscore_reversion": 1728,
        "rsi_extreme": 2592,
    }
    assert sum(counts.values()) == 8208


def test_v05_momentum_grid_count_and_plugins_load():
    raw = _load_yaml("search_v0.5_momentum_trend.yaml")
    counts = _grid_counts(raw)

    assert counts == {
        "rsi_momentum": 1458,
        "roc_momentum": 2592,
        "macd_momentum": 1944,
        "ema_cross": 648,
        "ema_slope_pullback": 4374,
    }
    assert sum(counts.values()) == 11016


def test_v04_and_v05_keep_locked_splits_costs_and_predeclared_gates():
    for filename in (
        "search_v0.4_mean_reversion.yaml",
        "search_v0.5_momentum_trend.yaml",
    ):
        raw = _load_yaml(filename)

        assert raw["data"]["splits"]["train"] == {
            "start": "2021-01-01T00:00:00Z",
            "end": "2024-07-01T00:00:00Z",
            "locked": False,
        }
        assert raw["data"]["splits"]["validation"] == {
            "start": "2024-07-01T00:00:00Z",
            "end": "2025-07-01T00:00:00Z",
            "locked": False,
        }
        assert raw["data"]["splits"]["final_oos"]["locked"] is True

        assert raw["engine"] == {
            "fee_per_side": 0.0005,
            "slippage_per_side": 0.0002,
            "cancel_pending_on_new_day": True,
        }
        assert raw["search"]["shortlist_file"] is None

        selection = raw["selection"]
        assert selection["min_expectancy_r"] == 0.15
        assert selection["strict_expectancy"] is True
        assert selection["min_trades"] == 300
        assert selection["min_profit_factor"] == 1.3
        assert selection["max_cost_share_of_gross_wins"] == 0.40
        assert selection["by_split"]["validation"] == {
            "min_expectancy_r": 0.0,
            "strict_expectancy": True,
            "min_trades": 80,
            "min_profit_factor": 1.15,
        }


def test_every_v04_v05_plugin_prepares_and_encodes_a_declared_config():
    candles = _research_candles()

    for filename in (
        "search_v0.4_mean_reversion.yaml",
        "search_v0.5_momentum_trend.yaml",
    ):
        raw = _load_yaml(filename)
        for entry in raw["strategies"]:
            plugin = load_strategy_plugin(entry["plugin"])
            configs = plugin.expand_grid(entry["parameters"])
            assert configs

            config = configs[0]
            features = plugin.prepare_features(candles, [config])
            encoded = plugin.encode_parameters([config], features)

            assert features.float_features.shape[1] == len(candles.open)
            assert features.int_features.shape[1] == len(candles.open)
            assert encoded.float_params.shape[0] == 1
            assert encoded.int_params.shape[0] == 1


def test_execution_grids_match_the_family_hypotheses():
    v04 = _load_yaml("search_v0.4_mean_reversion.yaml")
    v05 = _load_yaml("search_v0.5_momentum_trend.yaml")

    v04_params = v04["strategies"][0]["parameters"]
    assert v04_params["risk_reward"] == [0.75, 1.0, 1.25, 1.5]
    assert v04_params["max_hold_bars"] == [16, 32, 64]
    assert v04_params["atr_stop_multiplier"] == [1.0, 1.5, 2.0]
    assert v04_params["side"] == ["both", "long", "short"]

    v05_params = v05["strategies"][0]["parameters"]
    assert v05_params["risk_reward"] == [2.0, 3.0, 4.0]
    assert v05_params["max_hold_bars"] == [96, 192, 384]
    assert v05_params["atr_stop_multiplier"] == [2.0, 3.0, 4.0]
    assert v05_params["side"] == ["both", "long", "short"]
