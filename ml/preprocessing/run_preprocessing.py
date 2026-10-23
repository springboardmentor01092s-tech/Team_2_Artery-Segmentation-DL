"""Command-line entry point for ARCADE preprocessing."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .pipeline import SPLITS, TASKS, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--task", choices=("all", *TASKS), default="all")
    parser.add_argument("--split", choices=("all", *SPLITS), default="all")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_pipeline(args.data_root, args.output_root,
                           TASKS if args.task == "all" else (args.task,),
                           SPLITS if args.split == "all" else (args.split,),
                           args.config, args.dry_run, args.force)
    print(json.dumps({"status": summary["status"], "issue_counts": summary["issue_counts"]}, indent=2))
    return 1 if summary["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
