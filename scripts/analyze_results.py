r"""Analyze an ExactBT run without rerunning the backtest.

Usage on Windows:
    .venv\Scripts\python.exe scripts\analyze_results.py results\train_xxxxxxxxxxxx

If RUN_DIR is omitted, the newest results/train_* directory is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _sort(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values(
        ["expectancy_R", "profit_factor_R", "max_drawdown_R", "trades"],
        ascending=[False, False, True, False],
        na_position="last",
    ).reset_index(drop=True)


def _gate_mask(frame: pd.DataFrame, selection: dict[str, Any]) -> pd.Series:
    mask = frame["trades"] >= int(selection.get("min_trades", 0))
    min_pf = selection.get("min_profit_factor")
    if min_pf is not None:
        mask &= frame["profit_factor_R"] >= float(min_pf)
    max_dd = selection.get("max_drawdown_r")
    if max_dd is not None:
        mask &= frame["max_drawdown_R"] <= float(max_dd)
    max_cost_share = selection.get("max_cost_share_of_gross_wins")
    if max_cost_share is not None:
        mask &= frame["cost_share_of_gross_wins"] <= float(max_cost_share)
    return mask


def _latest_train_run(root: Path) -> Path:
    runs = [path for path in root.glob("train_*") if (path / "all_results.parquet").exists()]
    if not runs:
        raise FileNotFoundError(f"No completed train run found under {root.resolve()}")
    return max(runs, key=lambda path: (path / "all_results.parquet").stat().st_mtime)


def _resolve_run(value: str | None) -> Path:
    if value:
        return Path(value).resolve()
    return _latest_train_run(Path("results"))


def _safe(value: Any, digits: int = 4) -> str:
    if pd.isna(value):
        return "n/a"
    if np.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{float(value):.{digits}f}"


def analyze(run_dir: Path, top: int) -> Path:
    all_path = run_dir / "all_results.parquet"
    summary_path = run_dir / "summary.json"
    if not all_path.exists() or not summary_path.exists():
        raise FileNotFoundError(f"Run is incomplete: {run_dir}")

    frame = _sort(pd.read_parquet(all_path))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = summary["manifest"]
    selection = manifest.get("effective_selection", manifest["config"]["selection"])
    threshold = float(selection.get("min_expectancy_r", 0.15))
    margin = float(selection.get("near_threshold_margin_r", 0.03))
    strict = bool(selection.get("strict_expectancy", True))

    gate_mask = _gate_mask(frame, selection)
    eligible = _sort(frame.loc[gate_mask].copy())
    pass_exp = frame["expectancy_R"] > threshold if strict else frame["expectancy_R"] >= threshold
    passing = _sort(frame.loc[gate_mask & pass_exp].copy())
    near = _sort(
        frame.loc[
            gate_mask
            & (frame["expectancy_R"] <= threshold)
            & (frame["expectancy_R"] >= threshold - margin)
        ].copy()
    )

    output = run_dir / "diagnostics"
    output.mkdir(parents=True, exist_ok=True)
    parameter_columns = [name for name in frame.columns if name.startswith("param_")]
    core_columns = [
        "strategy", "config_id", "parameters_json", "trades", "wins", "losses",
        "signals", "expectancy_R", "gross_expectancy_R", "avg_cost_R",
        "profit_factor_R", "max_drawdown_R", "cost_share_of_gross_wins",
    ]
    export_columns = [name for name in core_columns + parameter_columns if name in frame.columns]

    frame.head(top)[export_columns].to_csv(output / "top_raw.csv", index=False)
    eligible.head(top)[export_columns].to_csv(output / "top_eligible.csv", index=False)
    passing[export_columns].to_csv(output / "passing.csv", index=False)
    near[export_columns].to_csv(output / "near_threshold_eligible.csv", index=False)

    family_rows: list[dict[str, Any]] = []
    for strategy, group in frame.groupby("strategy", sort=True):
        active = group[group["trades"] > 0]
        eligible_group = _sort(group.loc[_gate_mask(group, selection)].copy())
        raw_best = _sort(group).iloc[0]
        eligible_best = None if eligible_group.empty else eligible_group.iloc[0]
        family_rows.append({
            "strategy": strategy,
            "configs": len(group),
            "configs_with_trades": len(active),
            "eligible_configs": len(eligible_group),
            "positive_net_active_configs": int((active["expectancy_R"] > 0.0).sum()),
            "positive_gross_active_configs": int((active["gross_expectancy_R"] > 0.0).sum()),
            "best_raw_expectancy_R": raw_best["expectancy_R"],
            "best_raw_trades": raw_best["trades"],
            "best_eligible_expectancy_R": np.nan if eligible_best is None else eligible_best["expectancy_R"],
            "best_eligible_gross_expectancy_R": np.nan if eligible_best is None else eligible_best["gross_expectancy_R"],
            "best_eligible_avg_cost_R": np.nan if eligible_best is None else eligible_best["avg_cost_R"],
            "best_eligible_profit_factor_R": np.nan if eligible_best is None else eligible_best["profit_factor_R"],
            "best_eligible_max_drawdown_R": np.nan if eligible_best is None else eligible_best["max_drawdown_R"],
            "best_eligible_trades": np.nan if eligible_best is None else eligible_best["trades"],
            "median_active_expectancy_R": active["expectancy_R"].median() if len(active) else np.nan,
            "median_active_cost_R": active["avg_cost_R"].median() if len(active) else np.nan,
        })
    family = pd.DataFrame(family_rows).sort_values(
        ["best_eligible_expectancy_R", "best_raw_expectancy_R"],
        ascending=False,
        na_position="last",
    )
    family.to_csv(output / "strategy_diagnostics.csv", index=False)

    sensitivity_rows: list[dict[str, Any]] = []
    for strategy, group in eligible.groupby("strategy", sort=True):
        for column in parameter_columns:
            if group[column].notna().sum() == 0:
                continue
            for value, bucket in group.groupby(column, dropna=True):
                sensitivity_rows.append({
                    "strategy": strategy,
                    "parameter": column.removeprefix("param_"),
                    "value": value,
                    "configs": len(bucket),
                    "median_expectancy_R": bucket["expectancy_R"].median(),
                    "best_expectancy_R": bucket["expectancy_R"].max(),
                    "median_gross_expectancy_R": bucket["gross_expectancy_R"].median(),
                    "median_avg_cost_R": bucket["avg_cost_R"].median(),
                    "median_trades": bucket["trades"].median(),
                })
    pd.DataFrame(sensitivity_rows).to_csv(output / "parameter_sensitivity.csv", index=False)

    lines = [
        "# ExactBT result diagnostics", "", f"- Run: `{run_dir}`",
        f"- Total configs: **{len(frame):,}**",
        f"- Configs with trades: **{int((frame['trades'] > 0).sum()):,}**",
        f"- Configs meeting sample/risk gates: **{len(eligible):,}**",
        f"- Passing configs: **{len(passing):,}**",
        f"- Eligible near threshold: **{len(near):,}**", "",
        "## Best sample-eligible configs", "",
    ]
    if eligible.empty:
        lines.append("No config meets the sample/risk gates.")
    else:
        lines.extend([
            "| Strategy | Trades | Net E | Gross E | Cost R | PF | DD R |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for _, row in eligible.head(20).iterrows():
            lines.append(
                f"| {row['strategy']} | {int(row['trades'])} | {_safe(row['expectancy_R'])} | "
                f"{_safe(row['gross_expectancy_R'])} | {_safe(row['avg_cost_R'])} | "
                f"{_safe(row['profit_factor_R'], 3)} | {_safe(row['max_drawdown_R'], 1)} |"
            )

    lines.extend(["", "## Strategy families", ""])
    lines.extend([
        "| Strategy | Configs | Eligible | Positive net | Best eligible E | Trades |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for _, row in family.iterrows():
        trades = "n/a" if pd.isna(row["best_eligible_trades"]) else str(int(row["best_eligible_trades"]))
        lines.append(
            f"| {row['strategy']} | {int(row['configs'])} | {int(row['eligible_configs'])} | "
            f"{int(row['positive_net_active_configs'])} | {_safe(row['best_eligible_expectancy_R'])} | {trades} |"
        )

    report_path = output / "diagnostics.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze an ExactBT result directory")
    parser.add_argument("run_dir", nargs="?", help="Completed results/<split_hash> directory")
    parser.add_argument("--top", type=int, default=250, help="Rows exported per top table")
    args = parser.parse_args()
    if args.top <= 0:
        parser.error("--top must be > 0")
    report = analyze(_resolve_run(args.run_dir), args.top)
    print(f"Diagnostics written to: {report}")


if __name__ == "__main__":
    main()
