"""
Deterministic Cartesian parameter-grid expansion.

Accepted YAML forms:
- scalar: 2.0
- explicit values: [1.0, 1.5, 2.0]
- numeric range: {start: 1.0, stop: 3.0, step: 0.25}

The stop value is inclusive when it falls on the step grid. No random or
heuristic sampling is used, which avoids silently skipping a listed config.
"""

from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np


def _expand_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        if not value:
            raise ValueError("Parameter list must not be empty.")
        return value

    if isinstance(value, dict) and {"start", "stop", "step"} <= set(value):
        start = float(value["start"])
        stop = float(value["stop"])
        step = float(value["step"])
        if step <= 0:
            raise ValueError("Range step must be > 0.")
        if stop < start:
            raise ValueError("Range stop must be >= start.")
        count = int(np.floor((stop - start) / step + 1e-12)) + 1
        values = [start + i * step for i in range(count)]
        if values[-1] < stop - 1e-12:
            values.append(stop)
        return [round(x, 12) for x in values]

    return [value]


def expand_parameter_grid(parameter_spec: dict[str, Any]) -> list[dict[str, Any]]:
    if not parameter_spec:
        return [{}]

    names = list(parameter_spec)
    value_lists = [_expand_value(parameter_spec[name]) for name in names]
    return [dict(zip(names, values, strict=True)) for values in product(*value_lists)]
