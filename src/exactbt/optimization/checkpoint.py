"""
Atomic checkpoint helpers.

Each completed batch is a separate Parquet file. Resume simply skips existing
batch files. Writes use a temporary sibling and os.replace(), so interruption
cannot leave a half-written file under the final checkpoint name.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


def atomic_write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.stem + ".tmp.parquet")
    frame.to_parquet(temp, index=False)
    os.replace(temp, path)


def atomic_write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)
    os.replace(temp, path)
