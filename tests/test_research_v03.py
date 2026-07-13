"""Focused tests for the v0.3 research strategies and reporting gates."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from conftest import make_candles
from exactbt.reporting import write_summary
from exactbt.strategies.price_action import PLUGIN as SWEEP_PLUGIN
from exactbt.strategies.research import ADX_EMA_PULLBACK_PLUGIN, DAILY_VWAP_RECLAIM_PLUGIN
from exactbt.strategies.strategy_indicators import daily_vwap
from exactbt.strategy_loader import load_strategy_plugin
from exactbt.indicators import IndicatorCache


def _research_candles(count: int = 420):
    x = np.arange(count, dtype=np.float64)
    close = 100.0 + 0.03 * x + 2.5 * np.sin(x / 9.0)
    open_ = close - 0.2 * np.sin(x / 3.0)
    high = np.maximum(open_, close) + 0.8
    low = np.minimum(open_, close) - 0.8
    candles = make_candles(open_.tolist(), high.tolist(), low.tolist(), close.tolist())
    volume = 100.0 + (x % 13.0) * 7.0
    candles.frame["volume"] = volume
    object.__setattr__(candles, "volume", np.ascontiguousarray(volume))
    return candles


def test_research_grid_count_and_plugins_load():
    project_root = Path(__file__).resolve().parents[1]
    raw = yaml.safe_load(
        (project_root / "config" / "search_v0.3_research.yaml").read_text(encoding="utf-8")
    )
    counts = {}
    for entry in raw["strategies"]:
        plugin = load_strategy_plugin(entry["plugin"])
        counts[plugin.name] = len(plugin.expand_grid(entry["parameters"]))

    assert counts == {
        "adx_ema_pullback": 1152,
        "daily_vwap_reclaim": 1728,
        "rolling_sweep_reclaim": 3456,
        "rolling_range_breakout": 3888,
    }
    assert sum(counts.values()) == 10224


def test_research_signal_plugins_prepare_and_encode():
    candles = _research_candles()
    cases = [
        (
            ADX_EMA_PULLBACK_PLUGIN,
            {
                "atr_stop_window": 14,
                "atr_stop_multiplier": 2.0,
                "risk_reward": 2.0,
                "max_hold_bars": 64,
                "side": "both",
                "fast_ema": 20,
                "slow_ema": 100,
                "adx_window": 14,
                "adx_threshold": 22,
                "pullback_lookback": 4,
                "require_di": True,
            },
        ),
        (
            DAILY_VWAP_RECLAIM_PLUGIN,
            {
                "atr_stop_window": 14,
                "atr_stop_multiplier": 2.0,
                "risk_reward": 2.0,
                "max_hold_bars": 64,
                "side": "both",
                "regime_ema": 100,
                "volume_window": 20,
                "volume_mult": 1.0,
                "vwap_slope_lookback": 4,
                "min_bars_after_reset": 4,
            },
        ),
    ]
    for plugin, config in cases:
        features = plugin.prepare_features(candles, [config])
        encoded = plugin.encode_parameters([config], features)
        assert features.float_features.shape[1] == len(candles.open)
        assert features.int_features.shape[1] == len(candles.open)
        assert encoded.float_params.shape[0] == 1
        assert encoded.int_params.shape[0] == 1


def test_daily_vwap_resets_at_utc_day():
    count = 100
    x = np.arange(count, dtype=np.float64)
    candles = make_candles(
        (100.0 + x).tolist(),
        (101.0 + x).tolist(),
        (99.0 + x).tolist(),
        (100.5 + x).tolist(),
    )
    vwap = daily_vwap(IndicatorCache(candles))
    typical = (candles.frame["high"] + candles.frame["low"] + candles.frame["close"]) / 3.0
    assert np.isclose(vwap.iloc[95], typical.iloc[:96].mean())
    assert np.isclose(vwap.iloc[96], typical.iloc[96])


def test_rolling_sweep_reclaim_uses_wick_stop():
    candles = make_candles(
        [100.0, 99.5],
        [101.0, 101.0],
        [99.0, 97.5],
        [100.0, 100.5],
    )
    feature_f = np.array(
        [
            [np.nan, 102.0],
            [np.nan, 98.0],
            [np.nan, 2.0],
            [np.nan, np.nan],
        ],
        dtype=np.float64,
    )
    params_f = np.array([0.0, 0.0, 0.25], dtype=np.float64)
    params_i = np.array([0, 1, 2, 3, 0, 0], dtype=np.int64)
    result = SWEEP_PLUGIN.step_nb(
        1,
        candles.open,
        candles.high,
        candles.low,
        candles.close,
        candles.volume,
        candles.day_id,
        feature_f,
        np.empty((0, 2), dtype=np.int8),
        params_f,
        params_i,
        np.empty(0, dtype=np.float64),
        np.empty(0, dtype=np.int64),
    )
    assert result[0] == 1
    assert np.isclose(result[1], 97.0)


def test_summary_separates_raw_and_sample_eligible(tmp_path: Path):
    rows = [
        {
            "strategy": "tiny_sample",
            "config_id": "raw",
            "trades": 1.0,
            "expectancy_R": 2.0,
            "gross_expectancy_R": 2.2,
            "avg_cost_R": 0.2,
            "profit_factor_R": np.inf,
            "max_drawdown_R": 0.0,
        },
        {
            "strategy": "eligible",
            "config_id": "eligible",
            "trades": 350.0,
            "expectancy_R": 0.10,
            "gross_expectancy_R": 0.20,
            "avg_cost_R": 0.10,
            "profit_factor_R": 1.2,
            "max_drawdown_R": 20.0,
        },
    ]
    all_results = pd.DataFrame(rows)
    eligible = all_results.iloc[[1]].copy()
    manifest = {
        "split_name": "train",
        "dataset_sha256": "test",
        "config": {"selection": {"min_trades": 300}},
    }
    write_summary(
        tmp_path,
        manifest,
        all_results,
        eligible,
        pd.DataFrame(columns=all_results.columns),
        pd.DataFrame(columns=all_results.columns),
    )
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["best_config"]["config_id"] == "eligible"
    assert payload["best_raw_config"]["config_id"] == "raw"
    text = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "REJECTED: insufficient sample" in text
