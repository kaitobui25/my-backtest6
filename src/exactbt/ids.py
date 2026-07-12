"""
Deterministic hashing for datasets, runs, and individual configs.

Stable IDs prevent duplicate work and make checkpoints safe to resume. A config
ID includes strategy/version, parameters, split, transaction costs, engine
version, and dataset SHA-256.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .constants import ENGINE_VERSION


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def make_config_id(
    *,
    strategy_name: str,
    strategy_version: str,
    parameters: dict[str, Any],
    split_name: str,
    split_definition: dict[str, Any],
    fee_per_side: float,
    slippage_per_side: float,
    dataset_sha256: str,
) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "strategy": strategy_name,
        "strategy_version": strategy_version,
        "parameters": parameters,
        "split_name": split_name,
        "split": split_definition,
        "fee_per_side": fee_per_side,
        "slippage_per_side": slippage_per_side,
        "dataset_sha256": dataset_sha256,
    }
    return stable_hash(payload)[:24]
