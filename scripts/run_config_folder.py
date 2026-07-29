from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class FolderRunError(RuntimeError):
    pass


@dataclass(frozen=True)
class BaseConfig:
    source: Path
    raw: dict[str, Any]
    data_path: Path
    output_root: Path


@dataclass(frozen=True)
class PreparedRun:
    base: BaseConfig
    split_name: str
    run_path: Path
    source_result: Path | None
    shortlist_path: Path | None
    shortlist_count: int | None


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_project_path(config_path: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    # Giong src/exactbt/workflow.py::_resolve_project_path.
    return (config_path.parent.parent / candidate).resolve()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise FolderRunError(f"YAML root phai la mapping: {path}")
    for section in ("data", "engine", "search", "selection", "strategies"):
        if section not in raw:
            raise FolderRunError(f"Thieu block '{section}' trong: {path}")
    return raw


def choose_parquet(expected: Path) -> Path:
    folder = expected.parent
    if not folder.is_dir():
        raise FolderRunError(
            "Khong tim thay folder dataset:\n"
            f"  Expected file : {expected}\n"
            f"  Dataset folder: {folder}"
        )

    candidates = [path.resolve() for path in folder.glob("*.parquet") if path.is_file()]
    if not candidates:
        raise FolderRunError(
            "Folder dataset khong co file .parquet:\n"
            f"  Expected file : {expected}\n"
            f"  Dataset folder: {folder}"
        )

    token = folder.name.upper()
    matching = [path for path in candidates if f"_{token}_" in path.name.upper()]
    pool = matching or candidates

    def sort_key(path: Path) -> tuple[str, float, str]:
        dates = re.findall(r"(?<!\d)(20\d{6})(?!\d)", path.name)
        latest_date = max(dates, default="")
        return latest_date, path.stat().st_mtime, path.name.lower()

    return max(pool, key=sort_key)


def load_base_config(config_path: Path) -> BaseConfig:
    raw = load_yaml(config_path)
    data_value = str(raw["data"].get("file", "")).strip()
    if not data_value:
        raise FolderRunError(f"data.file rong trong: {config_path}")
    declared_data = resolve_project_path(config_path, data_value)
    data_path = declared_data if declared_data.is_file() else choose_parquet(declared_data)

    output_value = str(raw["search"].get("output_dir", "results")).strip() or "results"
    output_root = resolve_project_path(config_path, output_value)
    return BaseConfig(config_path, raw, data_path, output_root)


def config_sort_key(path: Path) -> tuple[int, str]:
    order = {"m5": 0, "m15": 1, "m30": 2, "h1": 3, "h2": 4, "h4": 5, "d1": 6}
    name = path.stem.lower()
    timeframe = next(
        (tf for tf in order if re.search(rf"(?:^|_){tf}(?:_|$)", name)),
        "",
    )
    return order.get(timeframe, 99), name


def discover_configs(folder: Path) -> list[Path]:
    configs = {
        path.resolve()
        for pattern in ("search_*.yaml", "search_*.yml")
        for path in folder.rglob(pattern)
        if path.is_file() and not path.name.startswith("_runtime_")
    }
    return sorted(configs, key=config_sort_key)


def config_folder_sort_key(item: tuple[Path, int]) -> tuple[int, tuple[int, ...], str]:
    folder, _ = item
    match = re.fullmatch(r"v(\d+(?:\.\d+)*)", folder.name.lower())
    if match:
        version = tuple(int(part) for part in match.group(1).split("."))
        return 1, version, folder.name.lower()
    return 0, (), folder.name.lower()


def discover_config_folders(root: Path) -> list[tuple[Path, int]]:
    config_root = root / "config"
    if not config_root.is_dir():
        raise FolderRunError(f"Khong tim thay folder config: {config_root}")

    found: list[tuple[Path, int]] = []
    for folder in config_root.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.name.lower() == "generated":
            continue
        count = len(discover_configs(folder))
        if count:
            found.append((folder.resolve(), count))

    return sorted(found, key=config_folder_sort_key, reverse=True)


def choose_config_folder(root: Path) -> Path | None:
    folders = discover_config_folders(root)
    if not folders:
        raise FolderRunError("Khong tim thay folder con nao trong config co search YAML.")

    print("Chon folder config:")
    print("-" * 72)
    for index, (folder, count) in enumerate(folders, start=1):
        try:
            label = folder.relative_to(root)
        except ValueError:
            label = folder
        print(f"[{index}] {label}  |  {count} YAML")
    print("[0] Huy")

    while True:
        answer = input("Lua chon: ").strip()
        if answer == "0":
            return None
        if answer.isdigit():
            choice = int(answer)
            if 1 <= choice <= len(folders):
                return folders[choice - 1][0]
        print("Lua chon khong hop le.")


def choose_split() -> str | None:
    print()
    print("Chon che do cho ca folder:")
    print("-" * 72)
    print("[1] TRAIN")
    print("[2] VALIDATION  (lay passing_results tu TRAIN tuong ung)")
    print("[3] FINAL OOS   (lay passing_results tu VALIDATION tuong ung)")
    print("[0] Huy")
    mapping = {"1": "train", "2": "validation", "3": "final_oos", "0": None}
    while True:
        answer = input("Lua chon: ").strip()
        if answer in mapping:
            return mapping[answer]
        print("Lua chon khong hop le.")


def normalized_identity(raw: dict[str, Any]) -> dict[str, Any]:
    identity = copy.deepcopy(raw)
    data = identity.get("data")
    if isinstance(data, dict):
        data.pop("file", None)
        data.pop("active_split", None)
    search = identity.get("search")
    if isinstance(search, dict):
        search.pop("shortlist_file", None)
        search.pop("output_dir", None)
    return identity


def read_manifest(result_dir: Path) -> dict[str, Any] | None:
    manifest_path = result_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def find_source_result(base: BaseConfig, source_split: str) -> Path:
    output_root = base.output_root
    if not output_root.is_dir():
        raise FolderRunError(
            f"Chua co output folder cho {base.source.name}:\n  {output_root}\n"
            f"Hay chay {source_split.upper()} truoc."
        )

    wanted_identity = normalized_identity(base.raw)
    matches: list[Path] = []
    for result_dir in output_root.glob(f"{source_split}_*"):
        if not result_dir.is_dir():
            continue
        passing = result_dir / "passing_results.parquet"
        if not passing.is_file():
            continue
        manifest = read_manifest(result_dir)
        if manifest is None or str(manifest.get("split_name")) != source_split:
            continue
        manifest_config = manifest.get("config")
        if not isinstance(manifest_config, dict):
            continue
        if normalized_identity(manifest_config) == wanted_identity:
            matches.append(result_dir.resolve())

    if not matches:
        raise FolderRunError(
            f"Khong tim thay ket qua {source_split.upper()} dung config cho:\n"
            f"  {base.source}\n"
            f"Da tim trong:\n  {output_root}\n"
            "Co the config da thay doi sau khi chay split truoc; hay chay lai split truoc."
        )

    return max(matches, key=lambda path: (path.stat().st_mtime, path.name.lower()))


def freeze_passing_results(
    root: Path,
    base: BaseConfig,
    result_dir: Path,
    target_split: str,
) -> tuple[Path, int]:
    passing_file = result_dir / "passing_results.parquet"
    frame = pd.read_parquet(passing_file)
    if frame.empty:
        raise FolderRunError(
            f"{result_dir} khong co config passing. Khong the chay {target_split.upper()}."
        )

    required = {"strategy", "parameters_json"}
    missing = required - set(frame.columns)
    if missing:
        raise FolderRunError(
            f"{passing_file} thieu cot bat buoc: {sorted(missing)}"
        )

    configs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in frame.iterrows():
        strategy = str(row["strategy"])
        parameters = json.loads(str(row["parameters_json"]))
        if not isinstance(parameters, dict):
            raise FolderRunError(f"parameters_json khong phai object trong {passing_file}")
        stable = json.dumps(
            parameters,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        key = (strategy, stable)
        if key in seen:
            continue
        seen.add(key)
        configs.append({"strategy": strategy, "parameters": parameters})

    generated_dir = root / "config" / "generated" / "folder_runs" / base.source.parent.name
    generated_dir.mkdir(parents=True, exist_ok=True)
    output = generated_dir / (
        f"frozen_{base.source.stem}__{result_dir.name}__to_{target_split}.json"
    )
    manifest = read_manifest(result_dir) or {}
    payload = {
        "source": str(passing_file.resolve()),
        "source_split": manifest.get("split_name", "unknown"),
        "target_split": target_split,
        "number_of_configs": len(configs),
        "configs": configs,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output.resolve(), len(configs)


def prepare_run(
    root: Path,
    base: BaseConfig,
    split_name: str,
) -> PreparedRun:
    source_result: Path | None = None
    shortlist_path: Path | None = None
    shortlist_count: int | None = None

    if split_name != "train":
        source_split = "train" if split_name == "validation" else "validation"
        source_result = find_source_result(base, source_split)
        shortlist_path, shortlist_count = freeze_passing_results(
            root,
            base,
            source_result,
            split_name,
        )

    runtime = copy.deepcopy(base.raw)
    runtime["data"]["file"] = str(base.data_path)
    runtime["data"]["active_split"] = split_name
    runtime["search"]["output_dir"] = str(base.output_root)
    runtime["search"]["shortlist_file"] = (
        None if shortlist_path is None else str(shortlist_path)
    )

    run_path = base.source.with_name(f"_runtime_{base.source.stem}__{split_name}.yaml")
    run_path.write_text(
        yaml.safe_dump(runtime, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return PreparedRun(
        base=base,
        split_name=split_name,
        run_path=run_path,
        source_result=source_result,
        shortlist_path=shortlist_path,
        shortlist_count=shortlist_count,
    )


def print_command(command: list[str]) -> None:
    rendered = " ".join(f'"{part}"' if " " in part else part for part in command)
    print(f"  {rendered}")


def main() -> int:
    root = project_root()
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    if not python_exe.is_file():
        print(f"Khong tim thay Python: {python_exe}")
        return 1

    print("=" * 72)
    print("Chay tat ca config YAML trong folder")
    print("=" * 72)
    print()

    prepared: list[PreparedRun] = []
    try:
        folder = choose_config_folder(root)
        if folder is None:
            print("Da huy.")
            return 0

        split_name = choose_split()
        if split_name is None:
            print("Da huy.")
            return 0

        configs = discover_configs(folder)
        if not configs:
            raise FolderRunError(
                f"Khong tim thay search_*.yaml hoac search_*.yml trong:\n  {folder}"
            )

        bases = [load_base_config(config) for config in configs]

        # Preflight toan bo truoc. Neu mot timeframe thieu source result,
        # khong chay nua chung cac timeframe con lai.
        for base in bases:
            prepared.append(prepare_run(root, base, split_name))

        print()
        print(f"Folder : {folder.relative_to(root)}")
        print(f"Split  : {split_name.upper()}")
        print(f"Config : {len(prepared)}")
        print("-" * 72)
        for item in prepared:
            try:
                label = item.base.source.relative_to(root)
            except ValueError:
                label = item.base.source
            print(f"  {label}")
            print(f"      data  : {item.base.data_path}")
            print(f"      output: {item.base.output_root}")
            if item.source_result is not None:
                print(f"      source: {item.source_result}")
                print(f"      frozen: {item.shortlist_count} config")

        print()
        if split_name == "final_oos":
            confirmation = input(
                "Go OOS de mo khoa va chay FINAL OOS cho toan bo folder: "
            ).strip().upper()
            if confirmation != "OOS":
                print("Da huy FINAL OOS.")
                return 0
        else:
            answer = input(
                f"Chay tat ca tren {split_name.upper()}? [Y/n]: "
            ).strip().lower()
            if answer in {"n", "no"}:
                print("Da huy.")
                return 0

        for index, item in enumerate(prepared, start=1):
            print()
            print("=" * 72)
            print(
                f"[{index}/{len(prepared)}] "
                f"{item.base.source.name} - {split_name.upper()}"
            )
            print("=" * 72)

            command = [
                str(python_exe),
                "-m",
                "exactbt.cli",
                "search",
                "--config",
                str(item.run_path),
                "--split",
                split_name,
            ]
            if split_name == "final_oos":
                command.append("--unlock-final-oos")
            print("Lenh:")
            print_command(command)
            completed = subprocess.run(command, cwd=root, check=False)
            if completed.returncode != 0:
                print()
                print(f"[ERROR] Config failed with exit code {completed.returncode}:")
                print(f"  {item.base.source}")
                print("Batch stopped. Checkpoint da hoan thanh van duoc giu lai.")
                return completed.returncode

        print()
        print("=" * 72)
        print(f"Da chay xong {len(prepared)} config tren {split_name.upper()}:")
        print(f"  {folder}")
        print("=" * 72)
        return 0
    except (FolderRunError, OSError, ValueError, json.JSONDecodeError) as exc:
        print()
        print(f"[ERROR]\n{exc}")
        print("Runner chua bat dau hoac da dung an toan.")
        return 1
    finally:
        for item in prepared:
            try:
                item.run_path.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    sys.exit(main())
