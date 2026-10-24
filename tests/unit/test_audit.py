"""Traceability tests: physical CSV lines and exclusive dispositions."""

import csv
from pathlib import Path

from dataflow.generation.synthetic import generate
from dataflow.quality.audit import audit
from dataflow.quality.classify import classify


def test_full_audit_reconciles_with_classifier(tmp_path: Path) -> None:
    source = tmp_path / "input"
    generate(source)
    report = tmp_path / "reports" / "row_audit.csv"
    summary = audit(source, report)
    classified = classify(source)
    assert summary["input_rows"] == 100_000
    assert summary["accepted"] == classified.accepted == 94_618
    assert summary["duplicates"] == classified.duplicates == 3_006
    assert summary["invalid"] == classified.invalid == 1_176
    assert summary["conflicts"] == classified.conflicts == 1_200
    assert summary["invalid_reasons"] == classified.reasons

    with report.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 100_000
    assert [int(row["source_line"]) for row in rows] == list(range(2, 100_002))
    assert all(row["source_file"] == "sales.csv" for row in rows)
    assert all(
        not row["row_sha256"] and not row["key_sha256"]
        for row in rows if row["disposition"] == "invalid"
    )
    assert all(
        len(row["row_sha256"]) == 64 and len(row["key_sha256"]) == 64
        for row in rows if row["disposition"] != "invalid"
    )
    assert all(
        row["reason_code"] == "CONFLICTING_KEY"
        for row in rows if row["disposition"] == "conflict"
    )
