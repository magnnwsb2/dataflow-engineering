"""Command-line entry point for the deterministic NexaRetail pipeline."""

import argparse
import json
from pathlib import Path

from dataflow.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NexaRetail data pipeline")
    parser.add_argument("--workdir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    summary = run(args.workdir)
    print(json.dumps({
        "quality": summary["quality"],
        "initial_inserted": summary["initial_inserted"],
        "replay_inserted": summary["replay_inserted"],
        "persisted_sales": summary["persisted_sales"],
        "branches_reported": summary["branches_reported"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
