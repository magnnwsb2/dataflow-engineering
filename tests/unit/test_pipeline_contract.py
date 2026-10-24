"""Static contract checks for the end-to-end pipeline."""

from dataflow.pipeline import EXPECTED


def test_approved_quality_counts():
    assert EXPECTED == {
        "input_rows": 100_000,
        "accepted": 94_618,
        "duplicates": 3_006,
        "invalid": 1_176,
        "conflicts": 1_200,
    }
    assert EXPECTED["input_rows"] == sum(
        EXPECTED[key] for key in ("accepted", "duplicates", "invalid", "conflicts")
    )
