r"""Freeze selected TRAIN configurations for VALIDATION.

This copies strategy names + exact parameter dictionaries, not TRAIN config IDs,
because config IDs intentionally change with split boundaries.

Example:
    .venv\Scripts\python.exe scripts\freeze_shortlist.py ^
      results\train_xxxxxxxxxxxx ^
      --output config\shortlists\research_v03_train.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _gate_mask(frame: pd.DataFrame, selection: dict[str, Any]) -> pd.Series:
    mask = frame["trades"] >= int(selection.get("min_trades", 0))
    min_pf = selection.get("min_profit_factor")
    if min_pf is not None:
        mask &= frame["profit_factor_R"] >= float(min_pf)
    max_dd = selection.get("max_drawdown_r")
    if max_dd is not None:
        mask &= frame["max_drawdown_R"] <= float(max_dd)
    return mask


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze a TRAIN shortlist for validation")
    parser.add_argument("run_dir", help="Completed TRAIN result directory")
    parser.add_argument("--output", required=True, help="Destination JSON file")
    parser.add_argument(
        "--min-expectancy",
        type=float,
        default=None,
        help="Override TRAIN expectancy threshold; default uses run config",
    )
    parser.add_argument("--top-per-strategy", type=int, default=20)
    parser.add_argument("--max-total", type=int, default=100)
    args = parser.parse_args()

    if args.top_per_strategy <= 0 or args.max_total <= 0:
        parser.error("--top-per-strategy and --max-total must be > 0")

    run_dir = Path(args.run_dir).resolve()
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    manifest = summary["manifest"]
    if manifest.get("split_name") != "train":
        raise ValueError("Shortlists must be frozen from TRAIN only.")

    selection = manifest["config"]["selection"]
    threshold = (
        float(selection.get("min_expectancy_r", 0.15))
        if args.min_expectancy is None
        else args.min_expectancy
    )
    strict = bool(selection.get("strict_expectancy", True))

    frame = pd.read_parquet(run_dir / "all_results.parquet")
    mask = _gate_mask(frame, selection)
    expectancy_mask = (
        frame["expectancy_R"] > threshold
        if strict
        else frame["expectancy_R"] >= threshold
    )
    mask &= expectancy_mask
    candidates = frame.loc[mask].sort_values(
        ["expectancy_R", "profit_factor_R", "max_drawdown_R", "trades"],
        ascending=[False, False, True, False],
        na_position="last",
    )
    candidates = candidates.groupby("strategy", group_keys=False).head(args.top_per_strategy)
    candidates = candidates.head(args.max_total)
    if candidates.empty:
        raise RuntimeError(
            "No TRAIN config met the shortlist gates. Do not validate raw one-trade winners; "
            "inspect diagnostics or deliberately lower --min-expectancy."
        )

    configs = []
    for _, row in candidates.iterrows():
        configs.append(
            {
                "strategy": str(row["strategy"]),
                "parameters": json.loads(str(row["parameters_json"])),
                "train_config_id": str(row["config_id"]),
                "train_metrics": {
                    "trades": int(row["trades"]),
                    "expectancy_R": float(row["expectancy_R"]),
                    "gross_expectancy_R": float(row["gross_expectancy_R"]),
                    "avg_cost_R": float(row["avg_cost_R"]),
                    "profit_factor_R": float(row["profit_factor_R"]),
                    "max_drawdown_R": float(row["max_drawdown_R"]),
                },
            }
        )

    payload = {
        "format_version": 1,
        "source_run_id": manifest["run_id"],
        "source_dataset_sha256": manifest["dataset_sha256"],
        "source_split": manifest["split"],
        "threshold_used": threshold,
        "strict_expectancy": strict,
        "top_per_strategy": args.top_per_strategy,
        "max_total": args.max_total,
        "configs": configs,
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Frozen {len(configs)} TRAIN configs: {output}")


if __name__ == "__main__":
    main()
