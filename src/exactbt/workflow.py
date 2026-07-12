"""End-to-end exact parameter-search workflow.

Workflow responsibilities are orchestration only:
1. load and validate Parquet data;
2. enumerate every enabled strategy config deterministically;
3. optionally restrict a non-TRAIN run to a frozen TRAIN shortlist;
4. run the same exact Numba kernel in configurable batches;
5. checkpoint each batch atomically and resume completed work;
6. retain all exact metrics and sample-eligible diagnostics;
7. rerun selected configs in record mode and verify metric parity.

No approximate screening engine or heuristic early rejection is used.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numba import get_num_threads, set_num_threads

from .config import LoadedConfig
from .constants import ENGINE_VERSION, METRIC_NAMES
from .data import load_parquet, select_split, sha256_file
from .execution.kernel_factory import CompiledKernel, build_kernel
from .execution.results import metric_matrix_to_frame, records_to_frame
from .ids import make_config_id, stable_hash, stable_json
from .optimization.checkpoint import atomic_write_json, atomic_write_parquet
from .reporting import write_summary
from .strategy_loader import load_strategy_plugin
from .types import EncodedStrategyParameters, StrategyFeatures, StrategyPlugin


@dataclass
class StrategyRuntime:
    plugin_path: str
    plugin: StrategyPlugin
    configs: list[dict[str, Any]]
    config_ids: list[str]
    features: StrategyFeatures
    encoded: EncodedStrategyParameters
    kernel: CompiledKernel


def _resolve_project_path(config: LoadedConfig, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (config.path.parent.parent / candidate).resolve()


def _non_expectancy_mask(frame: pd.DataFrame, selection: dict[str, Any]) -> pd.Series:
    """Apply sample-size and optional risk gates, but not expectancy."""
    mask = frame["trades"] >= int(selection.get("min_trades", 0))
    min_pf = selection.get("min_profit_factor")
    if min_pf is not None:
        mask &= frame["profit_factor_R"] >= float(min_pf)
    max_dd = selection.get("max_drawdown_r")
    if max_dd is not None:
        mask &= frame["max_drawdown_R"] <= float(max_dd)
    return mask


def _selection_mask(frame: pd.DataFrame, selection: dict[str, Any]) -> pd.Series:
    threshold = float(selection.get("min_expectancy_r", 0.15))
    strict = bool(selection.get("strict_expectancy", True))
    expectancy_mask = (
        frame["expectancy_R"] > threshold
        if strict
        else frame["expectancy_R"] >= threshold
    )
    return _non_expectancy_mask(frame, selection) & expectancy_mask


def _sort_results(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values(
        ["expectancy_R", "profit_factor_R", "max_drawdown_R", "trades"],
        ascending=[False, False, True, False],
        na_position="last",
    ).reset_index(drop=True)


def _extract_common_arrays(configs: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    rr = np.ascontiguousarray(
        np.array([float(config.get("risk_reward", 2.0)) for config in configs], dtype=np.float64)
    )
    max_hold = np.ascontiguousarray(
        np.array([int(config.get("max_hold_bars", 0)) for config in configs], dtype=np.int64)
    )
    if np.any(rr <= 0):
        raise ValueError("Every risk_reward must be > 0.")
    if np.any(max_hold < 0):
        raise ValueError("Every max_hold_bars must be >= 0.")
    return rr, max_hold


def _load_shortlist(
    loaded: LoadedConfig,
    search_config: dict[str, Any],
) -> tuple[Path | None, set[tuple[str, str]] | None, str | None]:
    """Load a frozen TRAIN shortlist keyed by strategy name and parameters."""
    value = search_config.get("shortlist_file")
    if value in (None, "", False):
        return None, None, None

    path = _resolve_project_path(loaded, str(value))
    if not path.exists():
        raise FileNotFoundError(f"Shortlist file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("configs") if isinstance(payload, dict) else payload
    if not isinstance(entries, list) or not entries:
        raise ValueError("Shortlist must contain a non-empty 'configs' list.")

    allowed: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Shortlist entry {index} must be an object.")
        strategy = entry.get("strategy")
        parameters = entry.get("parameters")
        if not isinstance(strategy, str) or not isinstance(parameters, dict):
            raise ValueError(
                f"Shortlist entry {index} requires string 'strategy' and object 'parameters'."
            )
        key = (strategy, stable_json(parameters))
        if key in allowed:
            raise ValueError(f"Duplicate shortlist entry: {strategy} {parameters}")
        allowed.add(key)

    return path, allowed, sha256_file(path)


def run_search(
    loaded: LoadedConfig,
    *,
    split_name: str | None = None,
    unlock_final_oos: bool = False,
) -> Path:
    raw = loaded.raw
    data_config = raw["data"]
    engine_config = raw["engine"]
    search_config = raw["search"]
    selection_config = raw["selection"]

    split_name = split_name or str(data_config.get("active_split", "train"))
    data_path = _resolve_project_path(loaded, str(data_config["file"]))
    output_root = _resolve_project_path(loaded, str(search_config.get("output_dir", "results")))
    shortlist_path, shortlist_allowed, shortlist_sha256 = _load_shortlist(loaded, search_config)
    if shortlist_allowed is not None and split_name == "train":
        raise ValueError("A frozen shortlist must not be used to search TRAIN.")

    requested_threads = int(search_config.get("num_threads", 0))
    if requested_threads > 0:
        set_num_threads(requested_threads)

    print(f"Loading Parquet: {data_path}")
    full_candles = load_parquet(data_path, data_config.get("timestamp_column", "auto"))
    candles = select_split(full_candles, data_config, split_name, unlock_final_oos)
    dataset_sha256 = sha256_file(data_path)
    split_definition = data_config["splits"][split_name]

    manifest_basis = {
        "engine_version": ENGINE_VERSION,
        "config": raw,
        "split_name": split_name,
        "split": split_definition,
        "dataset_sha256": dataset_sha256,
        "shortlist_sha256": shortlist_sha256,
    }
    run_id = f"{split_name}_{stable_hash(manifest_basis)[:12]}"
    run_dir = output_root / run_id
    batch_dir = run_dir / "batches"
    trade_dir = run_dir / "trades"
    run_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        **manifest_basis,
        "run_id": run_id,
        "data_file": str(data_path),
        "candles": len(candles.open),
        "data_start": str(candles.frame["datetime"].iloc[0]),
        "data_end": str(candles.frame["datetime"].iloc[-1]),
        "numba_threads": get_num_threads(),
        "shortlist_file": None if shortlist_path is None else str(shortlist_path),
        "shortlist_configs": 0 if shortlist_allowed is None else len(shortlist_allowed),
    }
    atomic_write_json(manifest, run_dir / "manifest.json")
    shutil.copy2(loaded.path, run_dir / "run_config.yaml")
    if shortlist_path is not None:
        shutil.copy2(shortlist_path, run_dir / "frozen_shortlist.json")

    fee_per_side = float(engine_config.get("fee_per_side", 0.0005))
    slippage_per_side = float(engine_config.get("slippage_per_side", 0.0002))
    cancel_pending = bool(engine_config.get("cancel_pending_on_new_day", True))
    batch_size = int(search_config.get("batch_size", 48))

    runtimes: dict[str, StrategyRuntime] = {}
    batch_files: list[Path] = []
    matched_shortlist: set[tuple[str, str]] = set()
    kernel_cache: dict[tuple[int, int, int, int], CompiledKernel] = {}

    for strategy_entry in raw["strategies"]:
        if not bool(strategy_entry.get("enabled", True)):
            continue

        plugin_path = str(strategy_entry["plugin"])
        plugin = load_strategy_plugin(plugin_path)
        configs = plugin.expand_grid(strategy_entry.get("parameters", {}))
        if shortlist_allowed is not None:
            selected_configs: list[dict[str, Any]] = []
            for config in configs:
                key = (plugin.name, stable_json(config))
                if key in shortlist_allowed:
                    selected_configs.append(config)
                    matched_shortlist.add(key)
            configs = selected_configs

        if not configs:
            print(f"Skipping empty strategy grid: {plugin.name}")
            continue

        config_ids = [
            make_config_id(
                strategy_name=plugin.name,
                strategy_version=plugin.version,
                parameters=config,
                split_name=split_name,
                split_definition=split_definition,
                fee_per_side=fee_per_side,
                slippage_per_side=slippage_per_side,
                dataset_sha256=dataset_sha256,
            )
            for config in configs
        ]
        if len(config_ids) != len(set(config_ids)):
            raise ValueError(f"Duplicate configs detected in strategy {plugin.name}.")

        print(f"Preparing {plugin.name}: {len(configs):,} exact configs")
        features = plugin.prepare_features(candles, configs)
        encoded = plugin.encode_parameters(configs, features)
        if encoded.float_params.shape[0] != len(configs) or encoded.int_params.shape[0] != len(configs):
            raise ValueError(f"Encoded parameter row count mismatch for {plugin.name}.")

        kernel_key = (
            id(plugin.step_nb),
            id(plugin.reset_state_nb),
            int(plugin.state_float_size),
            int(plugin.state_int_size),
        )
        kernel = kernel_cache.get(kernel_key)
        if kernel is None:
            kernel = build_kernel(
                plugin.step_nb,
                plugin.reset_state_nb,
                plugin.state_float_size,
                plugin.state_int_size,
            )
            kernel_cache[kernel_key] = kernel
        runtimes[plugin.name] = StrategyRuntime(
            plugin_path=plugin_path,
            plugin=plugin,
            configs=configs,
            config_ids=config_ids,
            features=features,
            encoded=encoded,
            kernel=kernel,
        )

        rr_all, max_hold_all = _extract_common_arrays(configs)

        for start in range(0, len(configs), batch_size):
            end = min(start + batch_size, len(configs))
            checkpoint = batch_dir / f"{plugin.name}_{start:07d}_{end:07d}.parquet"
            batch_files.append(checkpoint)
            if checkpoint.exists():
                print(f"  resume: {checkpoint.name}")
                continue

            print(f"  exact batch {start:,}:{end:,}")
            matrix = kernel.batch_metrics_nb(
                candles.open,
                candles.high,
                candles.low,
                candles.close,
                candles.volume,
                candles.day_id,
                features.float_features,
                features.int_features,
                encoded.float_params[start:end],
                encoded.int_params[start:end],
                rr_all[start:end],
                fee_per_side,
                slippage_per_side,
                max_hold_all[start:end],
                cancel_pending,
            )
            result = metric_matrix_to_frame(matrix)
            result.insert(0, "parameters_json", [stable_json(c) for c in configs[start:end]])
            result.insert(0, "config_id", config_ids[start:end])
            result.insert(0, "strategy_version", plugin.version)
            result.insert(0, "strategy", plugin.name)
            for key in sorted({key for config in configs[start:end] for key in config}):
                result[f"param_{key}"] = [config.get(key) for config in configs[start:end]]
            result["cost_share_of_gross_wins"] = np.where(
                result["gross_wins"] * result["avg_gross_win_R"] > 0,
                result["cost_R_total"] / (result["gross_wins"] * result["avg_gross_win_R"]),
                np.nan,
            )
            atomic_write_parquet(result, checkpoint)

    if shortlist_allowed is not None:
        missing = shortlist_allowed - matched_shortlist
        if missing:
            examples = sorted(missing)[:5]
            raise ValueError(
                f"{len(missing)} shortlist configs were not found in enabled grids. Examples: {examples}"
            )

    existing_batches = [path for path in batch_files if path.exists()]
    if not existing_batches:
        raise RuntimeError("No strategy batches were produced.")

    all_results = pd.concat([pd.read_parquet(path) for path in existing_batches], ignore_index=True)
    if all_results["config_id"].duplicated().any():
        duplicates = all_results.loc[all_results["config_id"].duplicated(), "config_id"].tolist()
        raise RuntimeError(f"Duplicate config IDs in checkpoints: {duplicates[:10]}")
    all_results = _sort_results(all_results)
    atomic_write_parquet(all_results, run_dir / "all_results.parquet")

    eligible_mask = _non_expectancy_mask(all_results, selection_config)
    eligible = _sort_results(all_results.loc[eligible_mask].copy())
    atomic_write_parquet(eligible, run_dir / "eligible_results.parquet")

    passing = _sort_results(all_results.loc[_selection_mask(all_results, selection_config)].copy())
    atomic_write_parquet(passing, run_dir / "passing_results.parquet")

    threshold = float(selection_config.get("min_expectancy_r", 0.15))
    margin = float(selection_config.get("near_threshold_margin_r", 0.03))
    near = _sort_results(
        all_results.loc[
            eligible_mask
            & (all_results["expectancy_R"] <= threshold)
            & (all_results["expectancy_R"] >= threshold - margin)
        ].copy()
    )
    atomic_write_parquet(near, run_dir / "near_threshold_results.parquet")

    best_per_strategy = int(selection_config.get("keep_best_per_strategy", 20))
    family_best_raw = _sort_results(
        all_results.groupby("strategy", group_keys=False).head(best_per_strategy).copy()
    )
    atomic_write_parquet(family_best_raw, run_dir / "family_best_results.parquet")

    family_best_eligible = _sort_results(
        eligible.groupby("strategy", group_keys=False).head(best_per_strategy).copy()
    )
    atomic_write_parquet(family_best_eligible, run_dir / "family_best_eligible_results.parquet")

    detailed_candidates = pd.concat([passing, family_best_eligible, near], ignore_index=True)
    detailed_candidates = _sort_results(detailed_candidates.drop_duplicates("config_id"))
    detailed_limit = int(selection_config.get("detailed_records_max", 100))
    if detailed_limit > 0:
        detailed_candidates = detailed_candidates.head(detailed_limit)

    trade_dir.mkdir(parents=True, exist_ok=True)
    record_metric_rows: list[dict[str, Any]] = []
    result_by_id = all_results.set_index("config_id", drop=False)

    for _, selected in detailed_candidates.iterrows():
        config_id = str(selected["config_id"])
        strategy_name = str(selected["strategy"])
        runtime = runtimes[strategy_name]
        config_index = runtime.config_ids.index(config_id)
        config = runtime.configs[config_index]
        trade_path = trade_dir / f"{config_id}.parquet"

        metrics, record_i, record_f, record_count = runtime.kernel.one_with_records_nb(
            candles.open,
            candles.high,
            candles.low,
            candles.close,
            candles.volume,
            candles.day_id,
            runtime.features.float_features,
            runtime.features.int_features,
            runtime.encoded.float_params[config_index],
            runtime.encoded.int_params[config_index],
            float(config.get("risk_reward", 2.0)),
            fee_per_side,
            slippage_per_side,
            int(config.get("max_hold_bars", 0)),
            cancel_pending,
        )

        expected = result_by_id.loc[config_id, METRIC_NAMES].to_numpy(np.float64)
        finite = np.isfinite(expected) & np.isfinite(metrics)
        if not np.allclose(expected[finite], metrics[finite], rtol=0.0, atol=1e-12):
            raise RuntimeError(f"Metrics/record parity failure for config {config_id}.")
        if not np.array_equal(np.isnan(expected), np.isnan(metrics)):
            raise RuntimeError(f"NaN parity failure for config {config_id}.")

        trades = records_to_frame(candles, record_i, record_f, record_count)
        trades.insert(0, "config_id", config_id)
        trades.insert(0, "strategy", strategy_name)
        atomic_write_parquet(trades, trade_path)
        record_metric_rows.append(
            {
                "strategy": strategy_name,
                "config_id": config_id,
                "parameters_json": stable_json(config),
                **dict(zip(METRIC_NAMES, metrics, strict=True)),
            }
        )

    record_metrics = pd.DataFrame(
        record_metric_rows,
        columns=["strategy", "config_id", "parameters_json", *METRIC_NAMES],
    )
    atomic_write_parquet(record_metrics, run_dir / "record_mode_metrics.parquet")
    write_summary(run_dir, manifest, all_results, eligible, passing, near)

    print(f"Completed exact search: {run_dir}")
    print(
        f"Exact configs: {len(all_results):,}; eligible: {len(eligible):,}; passing: {len(passing):,}"
    )
    return run_dir
