"""Regression tests for authoritative order, SL/TP, gap, and re-entry rules."""

from __future__ import annotations

import numpy as np

from exactbt.constants import METRIC_INDEX
from exactbt.execution.results import records_to_frame
from conftest import make_candles


def _run(candles, signals, kernel, risk=1.0, rr=2.0):
    feature_i = np.ascontiguousarray(np.array([signals], dtype=np.int64))
    feature_f = np.empty((0, len(signals)), dtype=np.float64)
    metrics, record_i, record_f, count = kernel.one_with_records_nb(
        candles.open,
        candles.high,
        candles.low,
        candles.close,
        candles.volume,
        candles.day_id,
        feature_f,
        feature_i,
        np.array([risk], dtype=np.float64),
        np.empty(0, dtype=np.int64),
        rr,
        0.0,
        0.0,
        0,
        True,
    )
    return metrics, records_to_frame(candles, record_i, record_f, count)


def test_both_hit_uses_stop_and_entry_bar_is_checked(immediate_kernel):
    candles = make_candles(
        open_=[100.0, 100.0],
        high=[100.5, 103.0],
        low=[99.5, 98.0],
        close=[100.0, 101.0],
    )
    metrics, trades = _run(candles, [1, 0], immediate_kernel)
    assert len(trades) == 1
    assert trades.iloc[0]["entry_index"] == 1
    assert trades.iloc[0]["exit_index"] == 1
    assert trades.iloc[0]["exit_reason"] == "stop_loss_both_hit"
    assert trades.iloc[0]["gross_R"] == -1.0
    assert metrics[METRIC_INDEX["both_hit_count"]] == 1.0


def test_stop_gap_fills_at_open(immediate_kernel):
    candles = make_candles(
        open_=[100.0, 100.0, 98.0],
        high=[100.5, 100.5, 99.0],
        low=[99.5, 99.5, 97.0],
        close=[100.0, 100.0, 98.5],
    )
    _, trades = _run(candles, [1, 0, 0], immediate_kernel)
    assert trades.iloc[0]["stop_price"] == 99.0
    assert trades.iloc[0]["exit_price"] == 98.0
    assert trades.iloc[0]["exit_reason"] == "stop_gap"
    assert trades.iloc[0]["gross_R"] == -2.0


def test_no_same_candle_reentry_after_exit(immediate_kernel):
    candles = make_candles(
        open_=[100.0, 100.0, 100.0, 100.0, 100.0],
        high=[100.1, 103.0, 100.1, 103.0, 100.0],
        low=[99.9, 99.5, 99.9, 99.5, 100.0],
        close=[100.0, 102.0, 100.0, 102.0, 100.0],
    )
    _, trades = _run(candles, [1, 1, 1, 0, 0], immediate_kernel)
    assert len(trades) == 2
    assert trades.iloc[0]["signal_index"] == 0
    assert trades.iloc[0]["exit_index"] == 1
    # Signal on exit candle 1 was never scanned. Next valid signal is candle 2.
    assert trades.iloc[1]["signal_index"] == 2
    assert trades.iloc[1]["entry_index"] == 3


def test_cancelled_pending_entry_does_not_hide_new_day_candle(immediate_kernel):
    """A day-cancelled pending order must not suppress a fresh setup scan."""
    candles = make_candles(
        open_=[100.0, 100.0, 100.0],
        high=[100.2, 100.2, 100.2],
        low=[99.8, 99.8, 99.8],
        close=[100.0, 100.0, 100.0],
        day_ids=[1, 2, 2],
    )
    metrics, trades = _run(candles, [1, 1, 0], immediate_kernel)

    assert metrics[METRIC_INDEX["pending_cancelled_new_day"]] == 1.0
    assert len(trades) == 1
    assert trades.iloc[0]["signal_index"] == 1
    assert trades.iloc[0]["entry_index"] == 2
    assert trades.iloc[0]["exit_reason"] == "end_of_data"
