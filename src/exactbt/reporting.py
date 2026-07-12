"""Create machine-readable and human-readable ExactBT summaries.

Raw winners and sample-eligible winners are intentionally separated. A one-trade
configuration may be useful for debugging signal frequency, but it is never
presented as the best research candidate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .optimization.checkpoint import atomic_write_json


def _row_dict(frame: pd.DataFrame) -> dict[str, Any] | None:
    return None if frame.empty else frame.iloc[0].to_dict()


def _format_result(lines: list[str], title: str, row: dict[str, Any]) -> None:
    lines.extend(
        [
            "",
            f"## {title}",
            "",
            f"- Strategy: `{row['strategy']}`",
            f"- Config ID: `{row['config_id']}`",
            f"- Trades: `{int(row['trades'])}`",
            f"- Expectancy: `{row['expectancy_R']:.6f}R`",
            f"- Gross expectancy: `{row['gross_expectancy_R']:.6f}R`",
            f"- Average cost: `{row['avg_cost_R']:.6f}R`",
            f"- Profit factor: `{row['profit_factor_R']:.6f}`",
            f"- Max drawdown: `{row['max_drawdown_R']:.6f}R`",
        ]
    )


def write_summary(
    run_dir: Path,
    manifest: dict[str, Any],
    all_results: pd.DataFrame,
    eligible: pd.DataFrame,
    passing: pd.DataFrame,
    near_threshold: pd.DataFrame,
) -> None:
    raw_best = _row_dict(all_results)
    eligible_best = _row_dict(eligible)
    selection = manifest.get("effective_selection", manifest["config"]["selection"])
    min_trades = int(selection.get("min_trades", 0))

    payload = {
        "manifest": manifest,
        "total_configs": int(len(all_results)),
        "eligible_configs": int(len(eligible)),
        "passing_configs": int(len(passing)),
        "near_threshold_configs": int(len(near_threshold)),
        "best_config": eligible_best,
        "best_eligible_config": eligible_best,
        "best_raw_config": raw_best,
    }
    atomic_write_json(payload, run_dir / "summary.json")

    lines = [
        "# ExactBT Search Summary",
        "",
        f"- Split: `{manifest['split_name']}`",
        f"- Dataset SHA-256: `{manifest['dataset_sha256']}`",
        f"- Exact configs evaluated: **{len(all_results):,}**",
        f"- Configs meeting non-expectancy gates: **{len(eligible):,}**",
        f"- Configs passing full selection: **{len(passing):,}**",
        f"- Eligible near threshold: **{len(near_threshold):,}**",
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

    if eligible_best is None:
        lines.extend(
            [
                "",
                "## Best eligible result",
                "",
                f"No configuration met the non-expectancy gates, including `trades >= {min_trades}`.",
            ]
        )
    else:
        _format_result(lines, "Best eligible result", eligible_best)

    if raw_best is not None:
        _format_result(lines, "Best raw result — diagnostic only", raw_best)
        if int(raw_best["trades"]) < min_trades:
            lines.extend(
                [
                    "",
                    f"**REJECTED: insufficient sample (`{int(raw_best['trades'])}` < `{min_trades}` trades).**",
                ]
            )

    lines.extend(["", "## Best eligible by strategy", ""])
    if eligible.empty:
        lines.append("No strategy has a sample-eligible configuration.")
    else:
        family = eligible.groupby("strategy", group_keys=False).head(1)
        lines.extend(
            [
                "| Strategy | Trades | Expectancy R | Gross R | Cost R | PF | DD R |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, row in family.iterrows():
            lines.append(
                f"| {row['strategy']} | {int(row['trades'])} | "
                f"{row['expectancy_R']:.4f} | {row['gross_expectancy_R']:.4f} | "
                f"{row['avg_cost_R']:.4f} | {row['profit_factor_R']:.3f} | "
                f"{row['max_drawdown_R']:.1f} |"
            )

    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
