"""
Single authoritative execution-loop factory.

Each strategy supplies only two Numba functions:
- reset_state_nb(state_i, state_f)
- step_nb(...): advance setup logic for one eligible flat candle

This file owns every trading semantic shared by all strategies:
- signal on candle i enters at candle i+1 open;
- one position maximum, no pyramiding;
- setup scanning is disabled on every candle that contained a position;
- stop/target are checked on the entry candle;
- stop wins when stop and target are both touched;
- stop gaps fill at open, target gaps fill at target;
- no same-candle re-entry after exit;
- fees and slippage are deducted in R;
- metrics mode and record mode call the same `_simulate_one` function.

`fastmath` is deliberately disabled. Configs are parallelized, while candles
inside one config remain sequential because state at bar i depends on bar i-1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from numba import njit, prange

from exactbt.constants import (
    EXIT_END_OF_DATA,
    EXIT_MAX_HOLD,
    EXIT_STOP_BOTH_HIT,
    EXIT_STOP_GAP,
    EXIT_STOP_LOSS,
    EXIT_TAKE_PROFIT,
    METRIC_INDEX,
    METRIC_NAMES,
    STOP_ABSOLUTE_PRICE,
    STOP_DISTANCE,
    STOP_PERCENT,
)

# Integer trade-record rows.
REC_SIDE = 0
REC_SETUP_START = 1
REC_SIGNAL_INDEX = 2
REC_ENTRY_INDEX = 3
REC_EXIT_INDEX = 4
REC_EXIT_REASON = 5
RECORD_INT_NAMES = [
    "side",
    "setup_start_index",
    "signal_index",
    "entry_index",
    "exit_index",
    "exit_reason_code",
]

# Float trade-record rows.
REC_ENTRY_PRICE = 0
REC_STOP_PRICE = 1
REC_TARGET_PRICE = 2
REC_EXIT_PRICE = 3
REC_INITIAL_RISK = 4
REC_GROSS_R = 5
REC_COST_R = 6
REC_NET_R = 7
RECORD_FLOAT_NAMES = [
    "entry_price",
    "stop_price",
    "target_price",
    "exit_price",
    "initial_risk",
    "gross_R",
    "cost_R",
    "net_R",
]

METRIC_COUNT = len(METRIC_NAMES)
RECORD_INT_COUNT = len(RECORD_INT_NAMES)
RECORD_FLOAT_COUNT = len(RECORD_FLOAT_NAMES)

# Metric indexes become compile-time integers inside Numba functions.
M_TRADES = METRIC_INDEX["trades"]
M_WINS = METRIC_INDEX["wins"]
M_LOSSES = METRIC_INDEX["losses"]
M_DRAWS = METRIC_INDEX["draws"]
M_GROSS_WINS = METRIC_INDEX["gross_wins"]
M_GROSS_LOSSES = METRIC_INDEX["gross_losses"]
M_LONG = METRIC_INDEX["long_trades"]
M_SHORT = METRIC_INDEX["short_trades"]
M_SIGNALS = METRIC_INDEX["signals"]
M_INVALID = METRIC_INDEX["invalid_entries"]
M_PENDING_DAY = METRIC_INDEX["pending_cancelled_new_day"]
M_GROSS_TOTAL = METRIC_INDEX["gross_R_total"]
M_COST_TOTAL = METRIC_INDEX["cost_R_total"]
M_NET_TOTAL = METRIC_INDEX["net_R_total"]
M_EXPECTANCY = METRIC_INDEX["expectancy_R"]
M_GROSS_EXPECTANCY = METRIC_INDEX["gross_expectancy_R"]
M_AVG_COST = METRIC_INDEX["avg_cost_R"]
M_GROSS_WIN_RATE = METRIC_INDEX["gross_win_rate"]
M_AVG_GROSS_WIN = METRIC_INDEX["avg_gross_win_R"]
M_AVG_GROSS_LOSS = METRIC_INDEX["avg_gross_loss_R"]
M_WIN_RATE = METRIC_INDEX["win_rate"]
M_AVG_WIN = METRIC_INDEX["avg_win_R"]
M_AVG_LOSS = METRIC_INDEX["avg_loss_R"]
M_PF = METRIC_INDEX["profit_factor_R"]
M_DD = METRIC_INDEX["max_drawdown_R"]
M_STOP = METRIC_INDEX["stop_loss_count"]
M_TP = METRIC_INDEX["take_profit_count"]
M_BOTH = METRIC_INDEX["both_hit_count"]
M_GAP = METRIC_INDEX["stop_gap_count"]
M_MAX_HOLD = METRIC_INDEX["max_hold_count"]
M_EOD = METRIC_INDEX["end_of_data_count"]


@dataclass(frozen=True)
class CompiledKernel:
    batch_metrics_nb: Callable[..., np.ndarray]
    one_with_records_nb: Callable[..., tuple[np.ndarray, np.ndarray, np.ndarray, int]]


def build_kernel(
    strategy_step_nb: Any,
    reset_strategy_state_nb: Any,
    state_float_size: int,
    state_int_size: int,
) -> CompiledKernel:
    """Build one compiled specialization while retaining a single loop source."""

    @njit(cache=False, fastmath=False)
    def _simulate_one(
        open_: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        day_id: np.ndarray,
        feature_f: np.ndarray,
        feature_i: np.ndarray,
        strategy_params_f: np.ndarray,
        strategy_params_i: np.ndarray,
        risk_reward: float,
        fee_per_side: float,
        slippage_per_side: float,
        max_hold_bars: int,
        cancel_pending_on_new_day: bool,
        record_enabled: bool,
        record_i: np.ndarray,
        record_f: np.ndarray,
    ) -> tuple[np.ndarray, int]:
        metrics = np.zeros(METRIC_COUNT, dtype=np.float64)
        state_i = np.empty(state_int_size, dtype=np.int64)
        state_f = np.empty(state_float_size, dtype=np.float64)
        reset_strategy_state_nb(state_i, state_f)

        pending_side = 0
        pending_stop_value = np.nan
        pending_stop_mode = STOP_ABSOLUTE_PRICE
        pending_signal_index = -1
        pending_setup_start = -1
        pending_day = -1

        position_side = 0
        signal_index = -1
        setup_start_index = -1
        entry_index = -1
        entry_price = np.nan
        stop_price = np.nan
        target_price = np.nan
        initial_risk = np.nan

        equity_r = 0.0
        equity_peak_r = 0.0
        positive_net_sum = 0.0
        negative_net_sum = 0.0
        positive_gross_sum = 0.0
        negative_gross_sum = 0.0
        record_count = 0
        trading_cost_rate = fee_per_side + slippage_per_side

        for i in range(len(open_)):
            # A pending signal can only execute at this candle's open.  A
            # cancelled/invalid pending entry does NOT consume the candle; the
            # strategy may inspect that candle while flat, matching the exact
            # next-bar execution semantics.
            opened_this_candle = False
            if pending_side != 0 and position_side == 0:
                if cancel_pending_on_new_day and day_id[i] != pending_day:
                    metrics[M_PENDING_DAY] += 1.0
                else:
                    candidate_entry = open_[i]
                    candidate_stop = pending_stop_value
                    if pending_stop_mode == STOP_DISTANCE:
                        if pending_side == 1:
                            candidate_stop = candidate_entry - pending_stop_value
                        else:
                            candidate_stop = candidate_entry + pending_stop_value
                    elif pending_stop_mode == STOP_PERCENT:
                        if pending_side == 1:
                            candidate_stop = candidate_entry * (1.0 - pending_stop_value)
                        else:
                            candidate_stop = candidate_entry * (1.0 + pending_stop_value)

                    candidate_risk = abs(candidate_entry - candidate_stop)
                    valid_stop = candidate_risk > 0.0
                    if pending_side == 1:
                        valid_stop = valid_stop and candidate_stop < candidate_entry
                    else:
                        valid_stop = valid_stop and candidate_stop > candidate_entry

                    candidate_target = (
                        candidate_entry
                        + pending_side * candidate_risk * risk_reward
                    )
                    valid_target = (
                        risk_reward > 0.0
                        and candidate_target > 0.0
                        and np.isfinite(candidate_target)
                    )

                    if valid_stop and valid_target:
                        position_side = pending_side
                        signal_index = pending_signal_index
                        setup_start_index = pending_setup_start
                        entry_index = i
                        entry_price = candidate_entry
                        stop_price = candidate_stop
                        initial_risk = candidate_risk
                        target_price = candidate_target
                        opened_this_candle = True
                        reset_strategy_state_nb(state_i, state_f)
                    else:
                        metrics[M_INVALID] += 1.0

                pending_side = 0
                pending_stop_value = np.nan
                pending_signal_index = -1
                pending_setup_start = -1
                pending_day = -1

            # This flag is captured before an intrabar exit. It enforces no
            # setup scan and no re-entry on a candle that contained a position.
            position_existed_for_candle = position_side != 0
            exit_reason = 0
            exit_price = np.nan

            if position_side == 1:
                if open_[i] <= stop_price:
                    exit_price = open_[i]
                    exit_reason = EXIT_STOP_GAP
                elif open_[i] >= target_price:
                    exit_price = target_price
                    exit_reason = EXIT_TAKE_PROFIT
                else:
                    stop_hit = low[i] <= stop_price
                    target_hit = high[i] >= target_price
                    if stop_hit and target_hit:
                        exit_price = stop_price
                        exit_reason = EXIT_STOP_BOTH_HIT
                    elif stop_hit:
                        exit_price = stop_price
                        exit_reason = EXIT_STOP_LOSS
                    elif target_hit:
                        exit_price = target_price
                        exit_reason = EXIT_TAKE_PROFIT
                    elif max_hold_bars > 0 and i - entry_index >= max_hold_bars:
                        exit_price = close[i]
                        exit_reason = EXIT_MAX_HOLD

            elif position_side == -1:
                if open_[i] >= stop_price:
                    exit_price = open_[i]
                    exit_reason = EXIT_STOP_GAP
                elif open_[i] <= target_price:
                    exit_price = target_price
                    exit_reason = EXIT_TAKE_PROFIT
                else:
                    stop_hit = high[i] >= stop_price
                    target_hit = low[i] <= target_price
                    if stop_hit and target_hit:
                        exit_price = stop_price
                        exit_reason = EXIT_STOP_BOTH_HIT
                    elif stop_hit:
                        exit_price = stop_price
                        exit_reason = EXIT_STOP_LOSS
                    elif target_hit:
                        exit_price = target_price
                        exit_reason = EXIT_TAKE_PROFIT
                    elif max_hold_bars > 0 and i - entry_index >= max_hold_bars:
                        exit_price = close[i]
                        exit_reason = EXIT_MAX_HOLD

            if exit_reason != 0:
                gross_r = position_side * (exit_price - entry_price) / initial_risk
                cost_r = (entry_price + exit_price) * trading_cost_rate / initial_risk
                net_r = gross_r - cost_r

                metrics[M_TRADES] += 1.0
                if position_side == 1:
                    metrics[M_LONG] += 1.0
                else:
                    metrics[M_SHORT] += 1.0

                if gross_r > 0.0:
                    metrics[M_GROSS_WINS] += 1.0
                    positive_gross_sum += gross_r
                elif gross_r < 0.0:
                    metrics[M_GROSS_LOSSES] += 1.0
                    negative_gross_sum += gross_r

                if net_r > 0.0:
                    metrics[M_WINS] += 1.0
                    positive_net_sum += net_r
                elif net_r < 0.0:
                    metrics[M_LOSSES] += 1.0
                    negative_net_sum += net_r
                else:
                    metrics[M_DRAWS] += 1.0

                metrics[M_GROSS_TOTAL] += gross_r
                metrics[M_COST_TOTAL] += cost_r
                metrics[M_NET_TOTAL] += net_r

                if exit_reason == EXIT_STOP_LOSS:
                    metrics[M_STOP] += 1.0
                elif exit_reason == EXIT_TAKE_PROFIT:
                    metrics[M_TP] += 1.0
                elif exit_reason == EXIT_STOP_BOTH_HIT:
                    metrics[M_BOTH] += 1.0
                elif exit_reason == EXIT_STOP_GAP:
                    metrics[M_GAP] += 1.0
                elif exit_reason == EXIT_MAX_HOLD:
                    metrics[M_MAX_HOLD] += 1.0

                equity_r += net_r
                if equity_r > equity_peak_r:
                    equity_peak_r = equity_r
                drawdown = equity_peak_r - equity_r
                if drawdown > metrics[M_DD]:
                    metrics[M_DD] = drawdown

                if record_enabled:
                    record_i[REC_SIDE, record_count] = position_side
                    record_i[REC_SETUP_START, record_count] = setup_start_index
                    record_i[REC_SIGNAL_INDEX, record_count] = signal_index
                    record_i[REC_ENTRY_INDEX, record_count] = entry_index
                    record_i[REC_EXIT_INDEX, record_count] = i
                    record_i[REC_EXIT_REASON, record_count] = exit_reason
                    record_f[REC_ENTRY_PRICE, record_count] = entry_price
                    record_f[REC_STOP_PRICE, record_count] = stop_price
                    record_f[REC_TARGET_PRICE, record_count] = target_price
                    record_f[REC_EXIT_PRICE, record_count] = exit_price
                    record_f[REC_INITIAL_RISK, record_count] = initial_risk
                    record_f[REC_GROSS_R, record_count] = gross_r
                    record_f[REC_COST_R, record_count] = cost_r
                    record_f[REC_NET_R, record_count] = net_r
                    record_count += 1

                position_side = 0

            if position_existed_for_candle or opened_this_candle:
                reset_strategy_state_nb(state_i, state_f)
                continue

            # The strategy only sees candles that were flat for the entire bar.
            side, stop_value, stop_mode, setup_start = strategy_step_nb(
                i,
                open_,
                high,
                low,
                close,
                volume,
                day_id,
                feature_f,
                feature_i,
                strategy_params_f,
                strategy_params_i,
                state_f,
                state_i,
            )
            if side != 0:
                metrics[M_SIGNALS] += 1.0
                pending_side = side
                pending_stop_value = stop_value
                pending_stop_mode = stop_mode
                pending_signal_index = i
                pending_setup_start = setup_start
                pending_day = day_id[i]

        # A position entered on the final candle is closed at final close.
        if position_side != 0:
            i = len(open_) - 1
            exit_price = close[i]
            exit_reason = EXIT_END_OF_DATA
            gross_r = position_side * (exit_price - entry_price) / initial_risk
            cost_r = (entry_price + exit_price) * trading_cost_rate / initial_risk
            net_r = gross_r - cost_r

            metrics[M_TRADES] += 1.0
            if position_side == 1:
                metrics[M_LONG] += 1.0
            else:
                metrics[M_SHORT] += 1.0
            if gross_r > 0.0:
                metrics[M_GROSS_WINS] += 1.0
                positive_gross_sum += gross_r
            elif gross_r < 0.0:
                metrics[M_GROSS_LOSSES] += 1.0
                negative_gross_sum += gross_r
            if net_r > 0.0:
                metrics[M_WINS] += 1.0
                positive_net_sum += net_r
            elif net_r < 0.0:
                metrics[M_LOSSES] += 1.0
                negative_net_sum += net_r
            else:
                metrics[M_DRAWS] += 1.0

            metrics[M_GROSS_TOTAL] += gross_r
            metrics[M_COST_TOTAL] += cost_r
            metrics[M_NET_TOTAL] += net_r
            metrics[M_EOD] += 1.0
            equity_r += net_r
            if equity_r > equity_peak_r:
                equity_peak_r = equity_r
            drawdown = equity_peak_r - equity_r
            if drawdown > metrics[M_DD]:
                metrics[M_DD] = drawdown

            if record_enabled:
                record_i[REC_SIDE, record_count] = position_side
                record_i[REC_SETUP_START, record_count] = setup_start_index
                record_i[REC_SIGNAL_INDEX, record_count] = signal_index
                record_i[REC_ENTRY_INDEX, record_count] = entry_index
                record_i[REC_EXIT_INDEX, record_count] = i
                record_i[REC_EXIT_REASON, record_count] = exit_reason
                record_f[REC_ENTRY_PRICE, record_count] = entry_price
                record_f[REC_STOP_PRICE, record_count] = stop_price
                record_f[REC_TARGET_PRICE, record_count] = target_price
                record_f[REC_EXIT_PRICE, record_count] = exit_price
                record_f[REC_INITIAL_RISK, record_count] = initial_risk
                record_f[REC_GROSS_R, record_count] = gross_r
                record_f[REC_COST_R, record_count] = cost_r
                record_f[REC_NET_R, record_count] = net_r
                record_count += 1

        trades = metrics[M_TRADES]
        if trades > 0.0:
            metrics[M_EXPECTANCY] = metrics[M_NET_TOTAL] / trades
            metrics[M_GROSS_EXPECTANCY] = metrics[M_GROSS_TOTAL] / trades
            metrics[M_AVG_COST] = metrics[M_COST_TOTAL] / trades
            metrics[M_GROSS_WIN_RATE] = metrics[M_GROSS_WINS] / trades
            metrics[M_WIN_RATE] = metrics[M_WINS] / trades
            if metrics[M_GROSS_WINS] > 0.0:
                metrics[M_AVG_GROSS_WIN] = positive_gross_sum / metrics[M_GROSS_WINS]
            if metrics[M_GROSS_LOSSES] > 0.0:
                metrics[M_AVG_GROSS_LOSS] = -negative_gross_sum / metrics[M_GROSS_LOSSES]
            if metrics[M_WINS] > 0.0:
                metrics[M_AVG_WIN] = positive_net_sum / metrics[M_WINS]
            if metrics[M_LOSSES] > 0.0:
                metrics[M_AVG_LOSS] = -negative_net_sum / metrics[M_LOSSES]
            if negative_net_sum < 0.0:
                metrics[M_PF] = positive_net_sum / -negative_net_sum
            elif positive_net_sum > 0.0:
                metrics[M_PF] = np.inf
            else:
                metrics[M_PF] = np.nan
        else:
            metrics[M_PF] = np.nan

        return metrics, record_count

    @njit(cache=False, parallel=True, fastmath=False)
    def batch_metrics_nb(
        open_: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        day_id: np.ndarray,
        feature_f: np.ndarray,
        feature_i: np.ndarray,
        strategy_params_f: np.ndarray,
        strategy_params_i: np.ndarray,
        risk_reward: np.ndarray,
        fee_per_side: float,
        slippage_per_side: float,
        max_hold_bars: np.ndarray,
        cancel_pending_on_new_day: bool,
    ) -> np.ndarray:
        config_count = strategy_params_f.shape[0]
        output = np.empty((config_count, METRIC_COUNT), dtype=np.float64)
        dummy_i = np.empty((RECORD_INT_COUNT, 1), dtype=np.int64)
        dummy_f = np.empty((RECORD_FLOAT_COUNT, 1), dtype=np.float64)

        for config_index in prange(config_count):
            metrics, _ = _simulate_one(
                open_, high, low, close, volume, day_id,
                feature_f, feature_i,
                strategy_params_f[config_index],
                strategy_params_i[config_index],
                risk_reward[config_index],
                fee_per_side,
                slippage_per_side,
                max_hold_bars[config_index],
                cancel_pending_on_new_day,
                False,
                dummy_i,
                dummy_f,
            )
            output[config_index] = metrics
        return output

    @njit(cache=False, fastmath=False)
    def one_with_records_nb(
        open_: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        day_id: np.ndarray,
        feature_f: np.ndarray,
        feature_i: np.ndarray,
        strategy_params_f: np.ndarray,
        strategy_params_i: np.ndarray,
        risk_reward: float,
        fee_per_side: float,
        slippage_per_side: float,
        max_hold_bars: int,
        cancel_pending_on_new_day: bool,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        record_i = np.empty((RECORD_INT_COUNT, len(open_)), dtype=np.int64)
        record_f = np.empty((RECORD_FLOAT_COUNT, len(open_)), dtype=np.float64)
        metrics, record_count = _simulate_one(
            open_, high, low, close, volume, day_id,
            feature_f, feature_i,
            strategy_params_f,
            strategy_params_i,
            risk_reward,
            fee_per_side,
            slippage_per_side,
            max_hold_bars,
            cancel_pending_on_new_day,
            True,
            record_i,
            record_f,
        )
        return metrics, record_i, record_f, record_count

    return CompiledKernel(
        batch_metrics_nb=batch_metrics_nb,
        one_with_records_nb=one_with_records_nb,
    )
