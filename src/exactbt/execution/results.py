"""
Convert raw metric/record arrays into labeled pandas tables.

No trading decisions are made here. This module only attaches names, timestamps,
and human-readable exit reasons to values already produced by the exact kernel.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from exactbt.constants import EXIT_REASON_NAMES, METRIC_NAMES
from exactbt.execution.kernel_factory import RECORD_FLOAT_NAMES, RECORD_INT_NAMES
from exactbt.types import CandleData


def metric_matrix_to_frame(matrix: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(matrix, columns=METRIC_NAMES)


def records_to_frame(
    candles: CandleData,
    record_i: np.ndarray,
    record_f: np.ndarray,
    record_count: int,
) -> pd.DataFrame:
    if record_count == 0:
        return pd.DataFrame(
            columns=[
                "direction",
                "setup_start_index",
                "setup_start_time",
                "signal_index",
                "signal_time",
                "entry_index",
                "entry_time",
                "entry_price",
                "stop_price",
                "target_price",
                "initial_risk",
                "exit_index",
                "exit_time",
                "exit_price",
                "exit_reason",
                "gross_R",
                "cost_R",
                "net_R",
            ]
        )

    ints = {name: record_i[row, :record_count] for row, name in enumerate(RECORD_INT_NAMES)}
    floats = {name: record_f[row, :record_count] for row, name in enumerate(RECORD_FLOAT_NAMES)}
    frame = pd.DataFrame({**ints, **floats})
    frame["direction"] = np.where(frame["side"] == 1, "LONG", "SHORT")
    frame["setup_start_time"] = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
    valid_setup = frame["setup_start_index"] >= 0
    frame.loc[valid_setup, "setup_start_time"] = pd.to_datetime(
        candles.timestamps_ns[frame.loc[valid_setup, "setup_start_index"].to_numpy(np.int64)],
        utc=True,
    )
    for prefix in ("signal", "entry", "exit"):
        index_column = f"{prefix}_index"
        frame[f"{prefix}_time"] = pd.to_datetime(
            candles.timestamps_ns[frame[index_column].to_numpy(np.int64)], utc=True
        )
    frame["exit_reason"] = frame["exit_reason_code"].map(EXIT_REASON_NAMES)

    return frame[
        [
            "direction",
            "setup_start_index",
            "setup_start_time",
            "signal_index",
            "signal_time",
            "entry_index",
            "entry_time",
            "entry_price",
            "stop_price",
            "target_price",
            "initial_risk",
            "exit_index",
            "exit_time",
            "exit_price",
            "exit_reason",
            "gross_R",
            "cost_R",
            "net_R",
        ]
    ]
