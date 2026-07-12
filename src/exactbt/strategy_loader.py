"""
Dynamic strategy plugin loading.

A strategy is enabled or disabled only through YAML. The `plugin` value uses
`module:attribute`, for example:
`exactbt.strategies.liquidity_sweep:PLUGIN`.
No central registry needs editing when a new strategy module is added.
"""

from __future__ import annotations

import importlib
from typing import Any

from .types import StrategyPlugin


def load_strategy_plugin(path: str) -> StrategyPlugin:
    if ":" not in path:
        raise ValueError(f"Strategy plugin must use module:attribute syntax: {path}")
    module_name, attribute = path.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    plugin: Any = getattr(module, attribute)

    required = (
        "name",
        "version",
        "state_float_size",
        "state_int_size",
        "step_nb",
        "reset_state_nb",
        "expand_grid",
        "prepare_features",
        "encode_parameters",
    )
    missing = [name for name in required if not hasattr(plugin, name)]
    if missing:
        raise TypeError(f"Plugin {path} is missing: {missing}")
    return plugin
