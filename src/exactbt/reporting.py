"""
Create concise machine-readable and human-readable run summaries.

The report highlights expectancy and its decomposition:
gross_expectancy_R - avg_cost_R = expectancy_R.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .optimization.checkpoint import atomic_write_json


def write_summary(
    run_dir: Path,
    manifest: dict[str, Any],
    all_results: pd.DataFrame,
    passing: pd.DataFrame,
    near_threshold: pd.DataFrame,
) -> None:
    best = None if all_results.empty else all_results.iloc[0].to_dict()
    payload = {
        "manifest": manifest,
        "total_configs": int(len(all_results)),
        "passing_configs": int(len(passing)),
        "near_threshold_configs": int(len(near_threshold)),
        "best_config": best,
    }
    atomic_write_json(payload, run_dir / "summary.json")

    lines = [
        "# ExactBT Search Summary",
        "",
        f"- Split: `{manifest['split_name']}`",
        f"- Dataset SHA-256: `{manifest['dataset_sha256']}`",
        f"- Exact configs evaluated: **{len(all_results):,}**",
        f"- Configs passing selection: **{len(passing):,}**",
        f"- Near threshold: **{len(near_threshold):,}**",
        "",
        "## Expectancy rule",
        "",
        "```text",
        "gross_expectancy_R = gross_win_rate × avg_gross_win_R",
        "                     - gross_loss_rate × avg_gross_loss_R",
        "expectancy_R = gross_expectancy_R - avg_cost_R",
        "source of truth = net_R_total / trades",
        "```",
    ]
    if best is not None:
        lines.extend(
            [
                "",
                "## Best exact result",
                "",
                f"- Strategy: `{best['strategy']}`",
                f"- Config ID: `{best['config_id']}`",
                f"- Trades: `{int(best['trades'])}`",
                f"- Expectancy: `{best['expectancy_R']:.6f}R`",
                f"- Gross expectancy: `{best['gross_expectancy_R']:.6f}R`",
                f"- Average cost: `{best['avg_cost_R']:.6f}R`",
                f"- Profit factor: `{best['profit_factor_R']:.6f}`",
                f"- Max drawdown: `{best['max_drawdown_R']:.6f}R`",
            ]
        )
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
