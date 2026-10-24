"""End-to-end acceptance test against a fresh ephemeral PostgreSQL database."""

import csv
import json

from dataflow.pipeline import EXPECTED, run
from dataflow.storage.connection import connect_from_env
from dataflow.storage.schema import apply_schema


def test_pipeline_reports_and_replay(tmp_path):
    with connect_from_env() as db:
        apply_schema(db)
        with db.transaction():
            db.execute("TRUNCATE fact_sale, rejected_row, pipeline_run, dim_product, dim_branch CASCADE")

    result = run(tmp_path)
    assert all(result["quality"][key] == value for key, value in EXPECTED.items())
    assert result["initial_inserted"] == 94_618
    assert result["replay_inserted"] == 0
    assert result["persisted_sales"] == 94_618
    assert result["branches_reported"] == 5

    reports = tmp_path / "reports"
    assert json.loads((reports / "quality_summary.json").read_text(encoding="utf-8")) == result["quality"]
    assert json.loads((reports / "run_summary.json").read_text(encoding="utf-8")) == result

    with (reports / "row_audit.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 100_000
    assert len({int(row["source_line"]) for row in rows}) == 100_000

    with (reports / "sales_by_branch.csv").open(encoding="utf-8", newline="") as handle:
        branches = list(csv.DictReader(handle))
    assert len(branches) == 5
    assert sum(int(row["unique_sales"]) for row in branches) == 94_618
