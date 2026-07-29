from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


TIMEFRAMES: tuple[tuple[str, str], ...] = (
    ("m5", "config/v0.6/search_v0.6_breakout_volatility_m5.yaml"),
    ("m15", "config/v0.6/search_v0.6_breakout_volatility_m15.yaml"),
    ("m30", "config/v0.6/search_v0.6_breakout_volatility_m30.yaml"),
    ("h1", "config/v0.6/search_v0.6_breakout_volatility_h1.yaml"),
    ("h2", "config/v0.6/search_v0.6_breakout_volatility_h2.yaml"),
    ("h4", "config/v0.6/search_v0.6_breakout_volatility_h4.yaml"),
)


class BatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedRun:
    timeframe: str
    source_dir: Path
    shortlist_path: Path
    config_path: Path
    config_count: int


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_status(status_log: Path | None, message: str) -> None:
    line = f"{timestamp()} {message}"
    if status_log is not None:
        status_log.parent.mkdir(parents=True, exist_ok=True)
        with status_log.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def read_manifest(result_dir: Path) -> dict[str, Any]:
    path = result_dir / "manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchError(f"Cannot read manifest: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BatchError(f"Manifest must be an object: {path}")
    return payload


def completed_result_dirs(result_root: Path, split_name: str) -> list[Path]:
    found: list[Path] = []
    if not result_root.exists():
        return found

    for path in result_root.glob(f"{split_name}_*"):
        if not path.is_dir():
            continue
        required = (
            path / "manifest.json",
            path / "summary.json",
            path / "passing_results.parquet",
        )
        if not all(item.is_file() for item in required):
            continue
        try:
            if str(read_manifest(path).get("split_name")) != split_name:
                continue
        except BatchError:
            continue
        found.append(path)

    def modified(path: Path) -> int:
        files = (
            path / "manifest.json",
            path / "summary.json",
            path / "passing_results.parquet",
        )
        return max(item.stat().st_mtime_ns for item in files)

    return sorted(found, key=lambda item: (modified(item), item.name), reverse=True)


def latest_completed_result(result_root: Path, split_name: str) -> Path | None:
    found = completed_result_dirs(result_root, split_name)
    return found[0] if found else None


def stable_parameters(raw: object) -> tuple[dict[str, Any], str]:
    try:
        parameters = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise BatchError(f"Invalid parameters_json: {raw!r}") from exc
    if not isinstance(parameters, dict):
        raise BatchError("parameters_json must decode to an object.")
    stable = json.dumps(
        parameters,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return parameters, stable


def freeze_passing_results(
    root: Path,
    timeframe: str,
    source_dir: Path,
    target_split: str,
) -> tuple[Path, int]:
    passing_path = source_dir / "passing_results.parquet"
    frame = pd.read_parquet(passing_path)
    if frame.empty:
        return Path(), 0

    required = {"strategy", "parameters_json"}
    missing = required - set(frame.columns)
    if missing:
        raise BatchError(
            f"{passing_path} is missing columns: {sorted(missing)}"
        )

    configs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in frame.iterrows():
        strategy = str(row["strategy"])
        parameters, stable = stable_parameters(row["parameters_json"])
        key = (strategy, stable)
        if key in seen:
            continue
        seen.add(key)
        configs.append({"strategy": strategy, "parameters": parameters})

    generated_dir = root / "config" / "generated" / "v0.6_timeframes" / timeframe
    generated_dir.mkdir(parents=True, exist_ok=True)
    output = generated_dir / f"frozen_{source_dir.name}_to_{target_split}.json"
    payload = {
        "source": source_dir.relative_to(root).as_posix(),
        "source_split": str(read_manifest(source_dir).get("split_name")),
        "target_split": target_split,
        "timeframe": timeframe,
        "number_of_configs": len(configs),
        "configs": configs,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output, len(configs)


def generated_config_path(base_yaml: Path, source_dir: Path, target_split: str) -> Path:
    return base_yaml.parent / (
        f"{base_yaml.stem}__{target_split}__from_{source_dir.name}.yaml"
    )


def create_split_config(
    root: Path,
    base_yaml: Path,
    shortlist_path: Path,
    source_dir: Path,
    target_split: str,
) -> Path:
    if not base_yaml.is_file():
        raise BatchError(f"Base YAML not found: {base_yaml}")

    output = generated_config_path(base_yaml, source_dir, target_split)
    resolver_base = output.parent.parent
    shortlist_value = os.path.relpath(shortlist_path, resolver_base).replace(os.sep, "/")
    yaml_value = json.dumps(shortlist_value, ensure_ascii=False)

    text = base_yaml.read_text(encoding="utf-8")
    pattern = re.compile(r"(?m)^([ \t]*shortlist_file[ \t]*:[ \t]*).*$")
    if pattern.search(text):
        text = pattern.sub(
            lambda match: f"{match.group(1)}{yaml_value}",
            text,
            count=1,
        )
    else:
        search_pattern = re.compile(r"(?m)^search[ \t]*:[ \t]*(?:#.*)?$")
        match = search_pattern.search(text)
        if match is None:
            raise BatchError(f"Missing search block in: {base_yaml}")
        insertion = f"{match.group(0)}\n  shortlist_file: {yaml_value}"
        text = text[: match.start()] + insertion + text[match.end() :]

    output.write_text(text, encoding="utf-8")

    resolved = (resolver_base / shortlist_value).resolve()
    if resolved != shortlist_path.resolve() or not resolved.is_file():
        raise BatchError(
            "Generated shortlist path failed preflight:\n"
            f"  config   : {output}\n"
            f"  value    : {shortlist_value}\n"
            f"  resolved : {resolved}\n"
            f"  expected : {shortlist_path.resolve()}"
        )
    return output


def prepare_run(
    root: Path,
    timeframe: str,
    base_yaml_relative: str,
    source_split: str,
    target_split: str,
) -> PreparedRun | None:
    result_root = root / "results" / "v0.6_timeframes" / timeframe
    source_dir = latest_completed_result(result_root, source_split)
    if source_dir is None:
        return None

    shortlist_path, config_count = freeze_passing_results(
        root,
        timeframe,
        source_dir,
        target_split,
    )
    if config_count == 0:
        return PreparedRun(timeframe, source_dir, Path(), Path(), 0)

    base_yaml = root / base_yaml_relative
    config_path = create_split_config(
        root,
        base_yaml,
        shortlist_path,
        source_dir,
        target_split,
    )
    return PreparedRun(
        timeframe=timeframe,
        source_dir=source_dir,
        shortlist_path=shortlist_path,
        config_path=config_path,
        config_count=config_count,
    )


def run_exactbt(root: Path, prepared: PreparedRun, target_split: str) -> None:
    command = [
        sys.executable,
        "-m",
        "exactbt.cli",
        "search",
        "--config",
        prepared.config_path.relative_to(root).as_posix(),
        "--split",
        target_split,
    ]
    if target_split == "final_oos":
        command.append("--unlock-final-oos")

    print("Command:")
    print("  " + " ".join(f'\"{part}\"' if " " in part else part for part in command))
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        raise BatchError(
            f"{prepared.timeframe.upper()} {target_split} failed "
            f"with exit code {completed.returncode}."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run v0.6 BTC timeframe validation or final OOS from frozen prior-split passing results."
    )
    parser.add_argument("split", choices=("validation", "final_oos"))
    parser.add_argument("--status-log", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root()
    status_log = Path(args.status_log).resolve() if args.status_log else None
    source_split = "train" if args.split == "validation" else "validation"
    target_split = str(args.split)

    completed_count = 0
    skipped_count = 0
    append_status(status_log, f"PHASE START {target_split}")

    print("=" * 72)
    print(f"ExactBT v0.6 - ALL BTC TIMEFRAMES - {target_split.upper()}")
    print(f"Source split: {source_split}")
    print("=" * 72)

    try:
        for timeframe, base_yaml_relative in TIMEFRAMES:
            print()
            print("-" * 72)
            print(f"Preparing {timeframe.upper()}: {source_split} -> {target_split}")
            print("-" * 72)
            append_status(
                status_log,
                f"START {timeframe.upper()} {source_split}->{target_split}",
            )

            prepared = prepare_run(
                root,
                timeframe,
                base_yaml_relative,
                source_split,
                target_split,
            )
            if prepared is None:
                message = (
                    f"SKIP {timeframe.upper()} no completed {source_split} result"
                )
                print(message)
                append_status(status_log, message)
                skipped_count += 1
                continue
            if prepared.config_count == 0:
                message = (
                    f"SKIP {timeframe.upper()} {prepared.source_dir.name} "
                    "has zero passing configs"
                )
                print(message)
                append_status(status_log, message)
                skipped_count += 1
                continue

            print(f"Source result : {prepared.source_dir}")
            print(f"Frozen configs: {prepared.config_count}")
            print(f"Shortlist     : {prepared.shortlist_path}")
            print(f"Generated YAML: {prepared.config_path}")
            run_exactbt(root, prepared, target_split)
            append_status(
                status_log,
                f"DONE {timeframe.upper()} {target_split} configs={prepared.config_count}",
            )
            completed_count += 1

    except (BatchError, OSError, ValueError, json.JSONDecodeError) as exc:
        print()
        print(f"[ERROR] {exc}")
        append_status(status_log, f"PHASE FAILED {target_split}: {exc}")
        return 1

    print()
    print("=" * 72)
    print(
        f"{target_split.upper()} PHASE FINISHED: "
        f"completed={completed_count}, skipped={skipped_count}"
    )
    print("=" * 72)
    append_status(
        status_log,
        f"PHASE DONE {target_split} completed={completed_count} skipped={skipped_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
