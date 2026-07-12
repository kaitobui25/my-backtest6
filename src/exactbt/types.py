"""
Small typed containers exchanged between data, strategy, and execution layers.

These classes live outside the hot Numba loop. They make module boundaries
explicit while keeping the compiled kernel limited to plain NumPy arrays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CandleData:
    frame: pd.DataFrame
    timestamps_ns: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    day_id: np.ndarray


@dataclass(frozen=True)
class StrategyFeatures:
    float_features: np.ndarray
    int_features: np.ndarray
    metadata: dict[str, Any]


@dataclass(frozen=True)
class EncodedStrategyParameters:
    float_params: np.ndarray
    int_params: np.ndarray


class StrategyPlugin(Protocol):
    name: str
    version: str
    state_float_size: int
    state_int_size: int
    step_nb: Any
    reset_state_nb: Any

    def expand_grid(self, parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def prepare_features(
        self,
        candles: CandleData,
        configs: list[dict[str, Any]],
    ) -> StrategyFeatures:
        ...

    def encode_parameters(
        self,
        configs: list[dict[str, Any]],
        features: StrategyFeatures,
    ) -> EncodedStrategyParameters:
        ...
