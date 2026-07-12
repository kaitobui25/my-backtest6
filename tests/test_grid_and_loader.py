"""Tests deterministic grids and dynamic strategy loading."""

from __future__ import annotations

from exactbt.optimization.grid import expand_parameter_grid
from exactbt.strategy_loader import load_strategy_plugin


def test_grid_is_cartesian_and_range_is_inclusive():
    configs = expand_parameter_grid(
        {
            "a": [1, 2],
            "b": {"start": 1.0, "stop": 1.5, "step": 0.25},
        }
    )
    assert len(configs) == 6
    assert configs[0] == {"a": 1, "b": 1.0}
    assert configs[-1] == {"a": 2, "b": 1.5}


def test_dynamic_strategy_loader():
    plugin = load_strategy_plugin("exactbt.strategies.liquidity_sweep:PLUGIN")
    assert plugin.name == "liquidity_sweep_reclaim"
