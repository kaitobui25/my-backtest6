"""
Command-line interface for ExactBT.

Examples:
    exactbt search --config config/search.yaml --split train
    exactbt search --config config/search.yaml --split validation

The locked final OOS split requires the explicit --unlock-final-oos flag.
"""

from __future__ import annotations

import argparse

from .config import load_config
from .workflow import run_search


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exact single-kernel batch backtester")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Run/resume exact parameter search")
    search.add_argument("--config", default="config/search.yaml")
    search.add_argument("--split", default=None)
    search.add_argument("--unlock-final-oos", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "search":
        loaded = load_config(args.config)
        run_search(
            loaded,
            split_name=args.split,
            unlock_final_oos=args.unlock_final_oos,
        )


if __name__ == "__main__":
    main()
