"""
Shared constants for the exact execution engine.

Keep numeric codes in one place so Numba kernels, reports, and tests interpret
results identically. Changing an execution rule requires bumping ENGINE_VERSION
because config IDs include this version.
"""

ENGINE_VERSION = "exactbt-single-kernel-v1"

# Stop specification returned by a strategy step.
STOP_ABSOLUTE_PRICE = 0
STOP_DISTANCE = 1
STOP_PERCENT = 2

# Exit reasons recorded by the kernel.
EXIT_NONE = 0
EXIT_STOP_LOSS = 1
EXIT_TAKE_PROFIT = 2
EXIT_STOP_BOTH_HIT = 3
EXIT_STOP_GAP = 4
EXIT_MAX_HOLD = 5
EXIT_END_OF_DATA = 6

EXIT_REASON_NAMES = {
    EXIT_NONE: "none",
    EXIT_STOP_LOSS: "stop_loss",
    EXIT_TAKE_PROFIT: "take_profit",
    EXIT_STOP_BOTH_HIT: "stop_loss_both_hit",
    EXIT_STOP_GAP: "stop_gap",
    EXIT_MAX_HOLD: "max_hold",
    EXIT_END_OF_DATA: "end_of_data",
}

# Float metric vector layout returned by every kernel run.
METRIC_NAMES = [
    "trades",
    "wins",
    "losses",
    "draws",
    "gross_wins",
    "gross_losses",
    "long_trades",
    "short_trades",
    "signals",
    "invalid_entries",
    "pending_cancelled_new_day",
    "gross_R_total",
    "cost_R_total",
    "net_R_total",
    "expectancy_R",
    "gross_expectancy_R",
    "avg_cost_R",
    "gross_win_rate",
    "avg_gross_win_R",
    "avg_gross_loss_R",
    "win_rate",
    "avg_win_R",
    "avg_loss_R",
    "profit_factor_R",
    "max_drawdown_R",
    "stop_loss_count",
    "take_profit_count",
    "both_hit_count",
    "stop_gap_count",
    "max_hold_count",
    "end_of_data_count",
]

METRIC_INDEX = {name: i for i, name in enumerate(METRIC_NAMES)}
