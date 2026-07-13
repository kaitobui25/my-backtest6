from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypeVar

import pandas as pd


RECENT_LIMIT = 3
T = TypeVar("T")


class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResultInfo:
    path: Path
    split_name: str
    total_configs: int | None
    passing_configs: int | None


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def ask_yes_no(prompt: str, *, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{prompt} {suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Nhap Y hoac N.")


def choose_from_recent(
    items: Sequence[T],
    *,
    title: str,
    label: Callable[[T], str],
    allow_manual_path: bool = False,
) -> T | Path | None:
    if not items and not allow_manual_path:
        return None

    show_all = False
    while True:
        print()
        print(title)
        print("-" * 72)
        visible = list(items if show_all else items[:RECENT_LIMIT])

        for index, item in enumerate(visible, start=1):
            print(f"[{index}] {label(item)}")

        option = len(visible) + 1
        more_available = len(items) > RECENT_LIMIT and not show_all
        if more_available:
            print(f"[{option}] Xem them")
            more_option = option
            option += 1
        else:
            more_option = None

        if allow_manual_path:
            manual_option = option
            print(f"[{manual_option}] Nhap duong dan khac")
        else:
            manual_option = None

        print("[0] Huy")
        answer = input("Lua chon: ").strip()
        if answer == "0":
            return None
        if not answer.isdigit():
            print("Lua chon khong hop le.")
            continue

        choice = int(answer)
        if 1 <= choice <= len(visible):
            return visible[choice - 1]
        if more_option is not None and choice == more_option:
            show_all = True
            continue
        if manual_option is not None and choice == manual_option:
            raw = input("Nhap folder result hoac passing_results.parquet: ").strip().strip('"')
            if raw:
                return Path(raw)
            print("Duong dan rong.")
            continue
        print("Lua chon khong hop le.")


def get_search_yamls(root: Path) -> list[Path]:
    config_dir = root / "config"
    candidates = set(config_dir.glob("search_*.yaml"))
    candidates |= set(config_dir.glob("search_*.yml"))

    base_yamls: list[Path] = []
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^\s*shortlist_file\s*:\s*([^#\r\n]*)", text)
        if match:
            value = match.group(1).strip().strip('"\'').lower()
            if value not in {"", "null", "none", "~"}:
                continue
        base_yamls.append(path)

    return sorted(
        base_yamls,
        key=lambda item: (item.stat().st_mtime, item.name.lower()),
        reverse=True,
    )


def yaml_label(root: Path, path: Path) -> str:
    stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return f"{path.relative_to(root)}  |  modified {stamp}"


def read_result_info(path: Path) -> ResultInfo:
    manifest_path = path / "manifest.json"
    summary_path = path / "summary.json"

    split_name = "unknown"
    total_configs: int | None = None
    passing_configs: int | None = None

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        split_name = str(manifest.get("split_name", split_name))

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        total = summary.get("total_configs")
        passing = summary.get("passing_configs")
        total_configs = int(total) if total is not None else None
        passing_configs = int(passing) if passing is not None else None
        if split_name == "unknown":
            nested_manifest = summary.get("manifest", {})
            split_name = str(nested_manifest.get("split_name", split_name))

    return ResultInfo(path, split_name, total_configs, passing_configs)


def get_result_dirs(root: Path, split_name: str) -> list[ResultInfo]:
    results_dir = root / "results"
    if not results_dir.exists():
        return []

    found: list[ResultInfo] = []
    for path in results_dir.glob(f"{split_name}_*"):
        if not path.is_dir() or not (path / "passing_results.parquet").exists():
            continue
        try:
            info = read_result_info(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if info.split_name == split_name:
            found.append(info)

    return sorted(
        found,
        key=lambda item: (item.path.stat().st_mtime, item.path.name.lower()),
        reverse=True,
    )


def result_label(root: Path, info: ResultInfo) -> str:
    total = "?" if info.total_configs is None else str(info.total_configs)
    passing = "?" if info.passing_configs is None else str(info.passing_configs)
    return f"{info.path.relative_to(root)}  |  total={total}, passing={passing}"


def normalize_result_path(root: Path, selected: ResultInfo | Path) -> Path:
    if isinstance(selected, ResultInfo):
        return selected.path.resolve()

    path = selected.expanduser()
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    if path.is_file():
        if path.name.lower() != "passing_results.parquet":
            raise RunnerError("Chi chap nhan folder result hoac passing_results.parquet.")
        path = path.parent
    if not path.is_dir():
        raise RunnerError(f"Khong tim thay folder result: {path}")
    return path


def confirm_source_result(root: Path, expected_split: str) -> Path | None:
    while True:
        selected = choose_from_recent(
            get_result_dirs(root, expected_split),
            title=f"Chon ket qua {expected_split.upper()} de dong bang",
            label=lambda item: result_label(root, item),
            allow_manual_path=True,
        )
        if selected is None:
            return None

        try:
            result_dir = normalize_result_path(root, selected)
            info = read_result_info(result_dir)
            if info.split_name != expected_split:
                raise RunnerError(
                    f"Result nay la split '{info.split_name}', can '{expected_split}'."
                )
            passing_file = result_dir / "passing_results.parquet"
            if not passing_file.exists():
                raise RunnerError(f"Thieu file: {passing_file}")
        except (RunnerError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"LOI: {exc}")
            continue

        print()
        print(f"Source result : {result_dir}")
        print(f"Split         : {info.split_name}")
        print(f"Passing       : {info.passing_configs if info.passing_configs is not None else '?'}")
        if ask_yes_no("Xac nhan dung ket qua nay?", default=True):
            return result_dir


def project_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def freeze_passing_results(
    root: Path,
    result_dir: Path,
    target_split: str,
) -> tuple[Path, int]:
    passing_file = result_dir / "passing_results.parquet"
    frame = pd.read_parquet(passing_file)
    if frame.empty:
        raise RunnerError(
            f"{result_dir.name} khong co config passing. Khong the chay {target_split}."
        )

    required = {"strategy", "parameters_json"}
    missing = required - set(frame.columns)
    if missing:
        raise RunnerError(f"passing_results.parquet thieu cot: {sorted(missing)}")

    configs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for _, row in frame.iterrows():
        strategy = str(row["strategy"])
        parameters = json.loads(str(row["parameters_json"]))
        if not isinstance(parameters, dict):
            raise RunnerError("parameters_json phai la JSON object.")
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

    generated_dir = root / "config" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    output = generated_dir / f"frozen_{result_dir.name}_to_{target_split}.json"
    payload = {
        "source": project_relative(root, passing_file),
        "source_split": read_result_info(result_dir).split_name,
        "target_split": target_split,
        "number_of_configs": len(configs),
        "configs": configs,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output, len(configs)


def create_split_config(
    root: Path,
    base_yaml: Path,
    shortlist: Path,
    split_name: str,
    source_dir: Path,
) -> Path:
    # ExactBT resolves relative paths from config_path.parent.parent.
    # Therefore generated YAML must stay directly under config/, not config/generated/.
    output = root / "config" / (
        f"{base_yaml.stem}__{split_name}__from_{source_dir.name}.yaml"
    )
    shortlist_value = project_relative(root, shortlist)
    yaml_value = json.dumps(shortlist_value, ensure_ascii=False)

    text = base_yaml.read_text(encoding="utf-8")
    shortlist_pattern = re.compile(
        r"(?m)^([ \t]*shortlist_file[ \t]*:[ \t]*).*$"
    )
    if shortlist_pattern.search(text):
        text = shortlist_pattern.sub(
            lambda match: f"{match.group(1)}{yaml_value}",
            text,
            count=1,
        )
    else:
        search_pattern = re.compile(r"(?m)^search[ \t]*:[ \t]*(?:#.*)?$")
        match = search_pattern.search(text)
        if not match:
            raise RunnerError(f"Khong tim thay block 'search:' trong {base_yaml}")
        insertion = f"{match.group(0)}\n  shortlist_file: {yaml_value}"
        text = text[: match.start()] + insertion + text[match.end() :]

    output.write_text(text, encoding="utf-8")
    verify_generated_config(root, output, shortlist)
    return output


def verify_generated_config(root: Path, config_path: Path, shortlist: Path) -> None:
    if config_path.parent.resolve() != (root / "config").resolve():
        raise RunnerError(
            "Generated YAML phai nam truc tiep trong config/ de ExactBT resolve path dung."
        )

    text = config_path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*shortlist_file\s*:\s*([^#\r\n]+)", text)
    if not match:
        raise RunnerError("Generated YAML khong co shortlist_file.")

    raw = match.group(1).strip().strip('"\'')
    candidate = Path(raw)
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (config_path.parent.parent / candidate).resolve()
    )
    if resolved != shortlist.resolve() or not resolved.exists():
        raise RunnerError(
            "Shortlist path preflight failed:\n"
            f"  YAML value : {raw}\n"
            f"  Resolved   : {resolved}\n"
            f"  Expected   : {shortlist.resolve()}"
        )


def choose_yaml(root: Path) -> Path | None:
    yamls = get_search_yamls(root)
    if not yamls:
        raise RunnerError(
            "Khong tim thay config/search_*.yaml base co shortlist_file null."
        )
    selected = choose_from_recent(
        yamls,
        title="Chon YAML search (mac dinh chi hien 3 file moi nhat)",
        label=lambda item: yaml_label(root, item),
    )
    return selected if isinstance(selected, Path) else None


def print_command(command: Iterable[str]) -> None:
    print()
    print("Lenh se chay:")
    print("  " + " ".join(f'"{part}"' if " " in part else part for part in command))


def latest_result_dir(root: Path, split_name: str) -> Path | None:
    results_dir = root / "results"
    if not results_dir.exists():
        return None
    dirs = [path for path in results_dir.glob(f"{split_name}_*") if path.is_dir()]
    return max(
        dirs,
        key=lambda path: (path.stat().st_mtime, path.name.lower()),
        default=None,
    )


def run_exactbt(
    root: Path,
    python_exe: Path,
    config_path: Path,
    split_name: str,
) -> None:
    command = [
        str(python_exe),
        "-m",
        "exactbt.cli",
        "search",
        "--config",
        project_relative(root, config_path),
        "--split",
        split_name,
    ]
    if split_name == "final_oos":
        command.append("--unlock-final-oos")

    print_command(command)
    if split_name == "final_oos":
        confirmation = input("Go OOS de mo khoa va chay FINAL OOS: ").strip().upper()
        if confirmation != "OOS":
            print("Da huy FINAL OOS.")
            return
    elif not ask_yes_no("Chay ngay?", default=True):
        print("Da huy.")
        return

    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        raise RunnerError(f"ExactBT ket thuc voi exit code {completed.returncode}.")

    result_dir = latest_result_dir(root, split_name)
    if result_dir is None:
        return
    print()
    print(f"Result folder: {result_dir}")
    summary = result_dir / "summary.md"
    if summary.exists():
        print()
        print(summary.read_text(encoding="utf-8"))


def choose_mode() -> str | None:
    print()
    print("Chon che do:")
    print("[1] TRAIN")
    print("[2] VALIDATION  (dong bang passing_results tu TRAIN)")
    print("[3] FINAL OOS   (dong bang passing_results tu VALIDATION)")
    print("[0] Thoat")
    mapping = {"1": "train", "2": "validation", "3": "final_oos", "0": None}
    while True:
        answer = input("Lua chon: ").strip()
        if answer in mapping:
            return mapping[answer]
        print("Lua chon khong hop le.")


def run_one(root: Path, python_exe: Path) -> bool:
    print_header("ExactBT Interactive Research Runner")
    mode = choose_mode()
    if mode is None:
        return False

    if mode == "train":
        yaml_path = choose_yaml(root)
        if yaml_path is not None:
            print(f"\nYAML: {yaml_path}")
            run_exactbt(root, python_exe, yaml_path, "train")
        return True

    source_split = "train" if mode == "validation" else "validation"
    source_dir = confirm_source_result(root, source_split)
    if source_dir is None:
        return True

    shortlist, config_count = freeze_passing_results(root, source_dir, mode)
    print(f"\nDa dong bang {config_count} config:")
    print(f"  {shortlist}")

    yaml_path = choose_yaml(root)
    if yaml_path is None:
        return True

    generated_config = create_split_config(
        root,
        yaml_path,
        shortlist,
        mode,
        source_dir,
    )
    print()
    print(f"Base YAML       : {yaml_path}")
    print(f"Frozen shortlist: {shortlist}")
    print(f"Generated YAML  : {generated_config}")
    print(f"Config count    : {config_count}")

    run_exactbt(root, python_exe, generated_config, mode)
    return True


def main() -> int:
    root = project_root()
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        print(f"Khong tim thay virtual environment: {python_exe}")
        print("Hay chay setup.bat truoc.")
        return 1

    try:
        while True:
            if not run_one(root, python_exe):
                return 0
            if not ask_yes_no("Chay tac vu khac?", default=False):
                return 0
    except KeyboardInterrupt:
        print("\nDa huy boi nguoi dung.")
        return 130
    except (RunnerError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"\nLOI: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
