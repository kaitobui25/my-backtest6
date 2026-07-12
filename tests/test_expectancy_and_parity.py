"""Tests expectancy decomposition and batch/record identity."""

from __future__ import annotations

import numpy as np
import pytest

from exactbt.constants import METRIC_INDEX
from conftest import make_candles


def test_expectancy_formula_and_batch_record_parity(immediate_kernel):
    # Trade 1 wins +2R gross. Trade 2 loses -1R gross.
    candles = make_candles(
        open_=[100.0, 100.0, 100.0, 100.0, 100.0],
        high=[100.1, 102.1, 100.1, 100.5, 100.0],
        low=[99.9, 99.5, 99.9, 98.9, 100.0],
        close=[100.0, 102.0, 100.0, 99.0, 100.0],
    )
    signals = np.array([[1, 0, 1, 0, 0]], dtype=np.int64)
    feature_f = np.empty((0, 5), dtype=np.float64)
    kernel = immediate_kernel

    fee = 0.0005
    slip = 0.0002
    batch = kernel.batch_metrics_nb(
        candles.open,
        candles.high,
        candles.low,
        candles.close,
        candles.volume,
        candles.day_id,
        feature_f,
        signals,
        np.array([[1.0]], dtype=np.float64),
        np.empty((1, 0), dtype=np.int64),
        np.array([2.0]),
        fee,
        slip,
        np.array([0], dtype=np.int64),
        True,
    )[0]

    record, _, _, count = kernel.one_with_records_nb(
        candles.open,
        candles.high,
        candles.low,
        candles.close,
        candles.volume,
        candles.day_id,
        feature_f,
        signals,
        np.array([1.0]),
        np.empty(0, dtype=np.int64),
        2.0,
        fee,
        slip,
        0,
        True,
    )
    assert count == 2
    assert np.allclose(batch, record, rtol=0.0, atol=0.0, equal_nan=True)

    gross_expectancy = batch[METRIC_INDEX["gross_expectancy_R"]]
    average_cost = batch[METRIC_INDEX["avg_cost_R"]]
    expectancy = batch[METRIC_INDEX["expectancy_R"]]
    assert expectancy == pytest.approx(gross_expectancy - average_cost)
    assert expectancy == pytest.approx(batch[METRIC_INDEX["net_R_total"]] / 2.0)
