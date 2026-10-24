"""Acceptance targets for deterministic synthetic inputs (T007–T008)."""

import csv
from collections import Counter
from pathlib import Path

from dataflow.generation.synthetic import generate


def test_generated_counts_and_reference_data(tmp_path: Path) -> None:
    manifest = generate(tmp_path)
    assert manifest["input_sales"] == 100_000
    assert manifest["expected_accepted"] == 94_618
    assert manifest["expected_duplicates"] == 3_006
    assert manifest["expected_invalid"] == 1_176
    assert manifest["expected_conflicts"] == 1_200
    assert manifest["expected_conflict_groups"] == 600
    assert sum(manifest["invalid_reasons"].values()) == 1_176
    assert sum(item["sales"] for item in manifest["per_branch"].values()) == 94_618
    with (tmp_path / "branches.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 5
    with (tmp_path / "products.csv").open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 200
    with (tmp_path / "sales.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 100_000
    groups = Counter((row["branch_id"], row["sale_id"]) for row in rows)
    assert sum(size == 2 for size in groups.values()) == 3_006 + 600
    assert max(groups.values()) == 2


def test_deterministic_output(tmp_path: Path) -> None:
    first = generate(tmp_path / "first")
    second = generate(tmp_path / "second")
    assert first == second
