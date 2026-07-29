from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreparedConfig:
    source: Path
    run_path: Path
    data_path: Path
    temporary: bool


class FolderRunError(RuntimeError):
    pass


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_input_path(root: Path, raw: str) -> Path:
    path = Path(raw.strip().strip('"')).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def find_data_file_line(text: str, config_path: Path) -> tuple[int, str, str]:
    lines = text.splitlines(keepends=True)
    data_index: int | None = None
    data_indent = 0

    for index, line in enumerate(lines):
        match = re.match(r"^([ \t]*)data[ \t]*:[ \t]*(?:#.*)?(?:\r?\n)?$", line)
        if match:
            data_index = index
            data_indent = len(match.group(1).expandtabs(4))
            break

    if data_index is None:
        raise FolderRunError(f"Khong tim thay block data: trong {config_path}")

    for index in range(data_index + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent_text = re.match(r"^([ \t]*)", line).group(1)
        indent = len(indent_text.expandtabs(4))
        if indent <= data_indent:
            break

        match = re.match(
            r"^([ \t]*file[ \t]*:[ \t]*)([^#\r\n]*)([ \t]*(?:#.*)?)(\r?\n)?$",
            line,
        )
        if match:
            raw_value = match.group(2).strip()
            if not raw_value:
                raise FolderRunError(f"data.file rong trong {config_path}")
            value = raw_value.strip("\"'")
            return index, match.group(1), value

    raise FolderRunError(f"Khong tim thay data.file trong {config_path}")


def resolve_declared_data(config_path: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    # Giong src/exactbt/workflow.py::_resolve_project_path.
    return (config_path.parent.parent / candidate).resolve()


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


def prepare_config(root: Path, config_path: Path) -> PreparedConfig:
    text = config_path.read_text(encoding="utf-8-sig")
    line_index, prefix, declared_value = find_data_file_line(text, config_path)
    declared_path = resolve_declared_data(config_path, declared_value)

    if declared_path.is_file():
        return PreparedConfig(config_path, config_path, declared_path, False)

    actual_path = choose_parquet(declared_path)
    lines = text.splitlines(keepends=True)
    original_line = lines[line_index]
    newline = "\r\n" if original_line.endswith("\r\n") else "\n"
    comment_match = re.search(r"([ \t]+#.*?)(?:\r?\n)?$", original_line)
    comment = comment_match.group(1) if comment_match else ""
    lines[line_index] = (
        f"{prefix}{json.dumps(str(actual_path), ensure_ascii=False)}{comment}{newline}"
    )

    runtime_path = config_path.with_name(f"_runtime_{config_path.stem}.yaml")
    runtime_path.write_text("".join(lines), encoding="utf-8")
    return PreparedConfig(config_path, runtime_path, actual_path, True)


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
        if path.is_file()
    }
    return sorted(configs, key=config_sort_key)


def print_command(command: list[str]) -> None:
    rendered = " ".join(f'"{part}"' if " " in part else part for part in command)
    print(f"  {rendered}")


def main() -> int:
    root = project_root()
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    if not python_exe.is_file():
        print(f"Khong tim thay Python: {python_exe}")
        return 1

    print("=" * 60)
    print("Chay tat ca config YAML trong folder - TRAIN")
    print("=" * 60)
    print()
    print("Vi du:")
    print(r"  config\v0.9")
    print()

    raw_folder = input("Nhap folder config: ").strip()
    if not raw_folder:
        print("Folder rong.")
        return 1

    folder = resolve_input_path(root, raw_folder)
    if not folder.is_dir():
        print(f"Khong tim thay folder: {folder}")
        return 1

    configs = discover_configs(folder)
    if not configs:
        print(f"Khong tim thay search_*.yaml hoac search_*.yml trong:\n  {folder}")
        return 1

    prepared: list[PreparedConfig] = []
    try:
        for config in configs:
            prepared.append(prepare_config(root, config))

        print()
        print(f"Tim thay {len(prepared)} config:")
        for item in prepared:
            try:
                config_label = item.source.relative_to(root)
            except ValueError:
                config_label = item.source
            status = "OK" if not item.temporary else "AUTO-RESOLVED"
            print(f"  [{status}] {config_label}")
            print(f"      data: {item.data_path}")

        print()
        answer = input("Chay tat ca tren TRAIN? [Y/n]: ").strip().lower()
        if answer in {"n", "no"}:
            print("Da huy.")
            return 0

        for index, item in enumerate(prepared, start=1):
            print()
            print("=" * 60)
            print(f"[{index}/{len(prepared)}] {item.source}")
            print("=" * 60)
            if item.temporary:
                print("Config khai bao sai ten file; dang dung config runtime:")
                print(f"  {item.run_path}")
                print("Dataset thuc te:")
                print(f"  {item.data_path}")

            command = [
                str(python_exe),
                "-m",
                "exactbt.cli",
                "search",
                "--config",
                str(item.run_path),
                "--split",
                "train",
            ]
            print("Lenh:")
            print_command(command)
            completed = subprocess.run(command, cwd=root, check=False)
            if completed.returncode != 0:
                print()
                print(f"[ERROR] Config failed with exit code {completed.returncode}:")
                print(f"  {item.source}")
                print("Batch stopped. Checkpoint da hoan thanh van duoc giu lai.")
                return completed.returncode

        print()
        print("=" * 60)
        print(f"Da chay xong {len(prepared)} config trong folder:")
        print(f"  {folder}")
        print("=" * 60)
        return 0
    except (FolderRunError, OSError) as exc:
        print()
        print(f"[DATA ERROR]\n{exc}")
        print("Runner chua bat dau; khong co config nao bi chay nua chung.")
        return 1
    finally:
        for item in prepared:
            if item.temporary:
                try:
                    item.run_path.unlink(missing_ok=True)
                except OSError:
                    pass


if __name__ == "__main__":
    sys.exit(main())
