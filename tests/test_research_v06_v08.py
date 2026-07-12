"""Configuration and plugin checks for ExactBT research v0.6-v0.8."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from conftest import make_candles
from exactbt.strategies.liquidity_sweep import PLUGIN as LIQUIDITY_PLUGIN
from exactbt.strategy_loader import load_strategy_plugin


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILES = (
    "search_v0.6_breakout_volatility.yaml",
    "search_v0.7_volume_confirmed.yaml",
    "search_v0.8_pdh_pdl_liquidity.yaml",
)


def _load_yaml(filename: str) -> dict:
    return yaml.safe_load((PROJECT_ROOT / "config" / filename).read_text(encoding="utf-8"))


def _grid_counts(raw: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in raw["strategies"]:
        plugin = load_strategy_plugin(entry["plugin"])
        assert plugin.name not in counts
        counts[plugin.name] = len(plugin.expand_grid(entry["parameters"]))
    return counts


def _research_candles(count: int = 620):
    x = np.arange(count, dtype=np.float64)
    close = 100.0 + 0.035 * x + 3.5 * np.sin(x / 13.0)
    open_ = close - 0.3 * np.sin(x / 5.0)
    high = np.maximum(open_, close) + 1.0
    low = np.minimum(open_, close) - 1.0
    candles = make_candles(open_.tolist(), high.tolist(), low.tolist(), close.tolist())

    volume = 100.0 + (x % 19.0) * 11.0
    candles.frame["volume"] = volume
    candles.frame["pdh"] = 125.0 + 0.01 * x
    candles.frame["pdl"] = 75.0 + 0.01 * x
    object.__setattr__(candles, "volume", np.ascontiguousarray(volume))
    return candles


def test_v06_grid_count_and_plugins_load():
    counts = _grid_counts(_load_yaml("search_v0.6_breakout_volatility.yaml"))
    assert counts == {
        "donchian_breakout": 288,
        "donchian_ema_atr": 576,
        "atr_expansion_breakout": 1728,
        "squeeze_breakout": 3456,
    }
    assert sum(counts.values()) == 6048


def test_v07_grid_count_and_plugins_load():
    counts = _grid_counts(_load_yaml("search_v0.7_volume_confirmed.yaml"))
    assert counts == {
        "breakout_volume": 1296,
        "momentum_volume": 5184,
    }
    assert sum(counts.values()) == 6480


def test_v08_grid_count_and_plugin_load():
    counts = _grid_counts(_load_yaml("search_v0.8_pdh_pdl_liquidity.yaml"))
    assert counts == {"liquidity_sweep_reclaim": 4860}


def test_v06_v08_keep_costs_splits_and_predeclared_gates():
    for filename in CONFIG_FILES:
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


def test_every_v06_v08_plugin_prepares_and_encodes_a_declared_config():
    candles = _research_candles()

    for filename in CONFIG_FILES:
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


def _liquidity_step(side: str | None):
    candles = make_candles(
        [109.0],
        [111.0],
        [101.0],
        [109.0],
    )
    candles.frame["pdh"] = [110.0]
    candles.frame["pdl"] = [100.0]

    config = {
        "sweep_buffer_ratio": 0.0,
        "reclaim_buffer_ratio": 0.0,
        "stop_buffer_ratio": 0.0,
        "max_wait_candles": 4,
        "risk_reward": 2.0,
        "max_hold_bars": 32,
    }
    if side is not None:
        config["side"] = side

    features = LIQUIDITY_PLUGIN.prepare_features(candles, [config])
    encoded = LIQUIDITY_PLUGIN.encode_parameters([config], features)
    state_f = np.empty(LIQUIDITY_PLUGIN.state_float_size, dtype=np.float64)
    state_i = np.empty(LIQUIDITY_PLUGIN.state_int_size, dtype=np.int64)
    LIQUIDITY_PLUGIN.reset_state_nb(state_i, state_f)

    result = LIQUIDITY_PLUGIN.step_nb(
        0,
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
    return result, encoded


def test_liquidity_side_filter_and_backward_compatibility():
    short_result, short_encoded = _liquidity_step("short")
    long_result, long_encoded = _liquidity_step("long")
    default_result, default_encoded = _liquidity_step(None)

    assert short_result[0] == -1
    assert np.isclose(short_result[1], 111.0)
    assert long_result[0] == 0
    assert default_result[0] == -1

    assert short_encoded.int_params.shape == (1, 2)
    assert short_encoded.int_params[0, 1] == -1
    assert long_encoded.int_params[0, 1] == 1
    assert default_encoded.int_params[0, 1] == 0
