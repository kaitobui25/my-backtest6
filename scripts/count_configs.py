"""
List enabled strategies and exact Cartesian config counts without loading data.

Run from the project directory after setup:
    python scripts/count_configs.py config/search.yaml

This is useful before a large search because it exposes accidental parameter
explosions while preserving the rule that every listed combination is tested.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from exactbt.strategy_loader import load_strategy_plugin


def main() -> None:
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config/search.yaml")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    total = 0
    print(f"Config: {config_path.resolve()}")
    print("-" * 72)
    for entry in raw["strategies"]:
        plugin = load_strategy_plugin(str(entry["plugin"]))
        enabled = bool(entry.get("enabled", True))
        count = len(plugin.expand_grid(entry.get("parameters", {}))) if enabled else 0
        total += count
        status = "ON " if enabled else "OFF"
        print(f"{status}  {plugin.name:<32} {count:>10,}")
    print("-" * 72)
    print(f"TOTAL EXACT CONFIGS: {total:,}")


if __name__ == "__main__":
    main()
