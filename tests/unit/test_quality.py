"""Quality acceptance checks for approved NexaRetail distribution."""

import csv
from pathlib import Path

import pytest

from dataflow.generation.synthetic import generate
from dataflow.quality.classify import classify, normalize


def test_full_approved_distribution(tmp_path: Path) -> None:
    generate(tmp_path)
    result = classify(tmp_path)
    assert (result.input_rows, result.accepted, result.duplicates, result.invalid, result.conflicts) == (
        100_000, 94_618, 3_006, 1_176, 1_200
    )
    assert result.reasons == {
        "MISSING_REQUIRED": 176,
        "INVALID_DATE": 200,
        "INVALID_MONEY": 200,
        "INVALID_QUANTITY": 150,
        "TOTAL_MISMATCH": 150,
        "UNKNOWN_BRANCH": 150,
        "UNKNOWN_PRODUCT": 150,
    }


def test_date_and_decimal_normalization() -> None:
    row = {
        "branch_id": "F001", "sale_id": "V00000001", "product_id": "P0001",
        "sale_date": "05/02/2026", "quantity": "2",
        "unit_price": "12,50", "total_amount": "25,00",
    }
    assert normalize(row, {"F001"}, {"P0001"}) == (
        "F001", "V00000001", "P0001", "2026-02-05", "2", "12.50", "25.00"
    )


def test_reject_wrong_total() -> None:
    row = {
        "branch_id": "F001", "sale_id": "V00000001", "product_id": "P0001",
        "sale_date": "2026-02-05", "quantity": "2",
        "unit_price": "12.50", "total_amount": "25.01",
    }
    with pytest.raises(ValueError, match="TOTAL_MISMATCH"):
        normalize(row, {"F001"}, {"P0001"})
