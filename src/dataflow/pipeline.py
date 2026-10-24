"""NexaRetail end-to-end pipeline: generate, audit, load, replay, export."""

import json
from pathlib import Path

from dataflow.analytics.report import branch_report
from dataflow.generation.synthetic import generate
from dataflow.quality.audit import audit
from dataflow.storage.connection import connect_from_env
from dataflow.storage.load import load
from dataflow.storage.schema import apply_schema

EXPECTED = {"input_rows": 100_000, "accepted": 94_618, "duplicates": 3_006,
            "invalid": 1_176, "conflicts": 1_200}


def run(workdir: Path) -> dict:
    """Run the deterministic batch and fail if reconciliation or replay differs."""
    workdir = Path(workdir)
    source = workdir / "input"
    reports = workdir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    manifest = generate(source)
    quality = audit(source, reports / "row_audit.csv")
    for name, expected in EXPECTED.items():
        if quality[name] != expected:
            raise ValueError(f"Quality reconciliation mismatch: {name}")

    with connect_from_env() as connection:
        apply_schema(connection)
        first = load(source, connection)
        if any(first[key] != value for key, value in EXPECTED.items()):
            raise ValueError("Database load reconciliation mismatch")
        if first["inserted"] != EXPECTED["accepted"]:
            raise ValueError("Initial load did not insert the expected number of sales")
        replay = load(source, connection)
        if replay["inserted"] != 0:
            raise ValueError("Idempotency replay inserted additional sales")
        count = connection.execute("SELECT COUNT(*) FROM fact_sale").fetchone()[0]
        if count != EXPECTED["accepted"]:
            raise ValueError("Persisted fact count mismatch")
        branches = branch_report(connection, reports / "sales_by_branch.csv")
        if sum(int(row["unique_sales"]) for row in branches) != count:
            raise ValueError("Gold sales count mismatch")
        if sum((row["revenue_brl"] != manifest["per_branch"][row["branch_id"]]["revenue"]
                for row in branches)):
            raise ValueError("Gold revenue mismatch")

    summary = {
        "quality": quality,
        "initial_inserted": first["inserted"],
        "replay_inserted": replay["inserted"],
        "persisted_sales": count,
        "branches_reported": len(branches),
        "generation_sha256": manifest["sha256"],
    }
    (reports / "quality_summary.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary
