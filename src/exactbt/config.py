"""
YAML configuration loading and validation.

The expectancy threshold is intentionally a normal config value rather than a
hard-coded rule. Default selection is strict expectancy_R > 0.15 and a minimum
trade count; extra gates remain optional to avoid discarding potentially useful
strategies too early.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class LoadedConfig:
    path: Path
    raw: dict[str, Any]


def load_config(path: str | Path) -> LoadedConfig:
    config_path = Path(path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    for section in ("data", "engine", "search", "selection", "strategies"):
        if section not in raw:
            raise ValueError(f"Missing required config section: {section}")

    if float(raw["selection"].get("min_expectancy_r", 0.15)) < -10:
        raise ValueError("min_expectancy_r is implausibly low.")

    batch_size = int(raw["search"].get("batch_size", 48))
    if batch_size <= 0:
        raise ValueError("search.batch_size must be > 0.")

    if not isinstance(raw["strategies"], list) or not raw["strategies"]:
        raise ValueError("At least one strategy entry is required.")

    return LoadedConfig(path=config_path, raw=raw)
