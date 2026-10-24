"""Independent acceptance verification of published, sanitized pipeline reports."""

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

EXPECTED = {
    "input_rows": 100_000,
    "accepted": 94_618,
    "duplicates": 3_006,
    "invalid": 1_176,
    "conflicts": 1_200,
}
DISPOSITIONS = {"accepted": "accepted", "duplicate": "duplicates",
                "invalid": "invalid", "conflict": "conflicts"}


def verify(reports: Path) -> dict:
    reports = Path(reports)
    quality = json.loads((reports / "quality_summary.json").read_text(encoding="utf-8"))
    run = json.loads((reports / "run_summary.json").read_text(encoding="utf-8"))
    counts = Counter()
    reasons = Counter()
    seen_lines = set()
    with (reports / "row_audit.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            disposition = row["disposition"]
            if disposition not in DISPOSITIONS:
                raise ValueError("Unknown audit disposition")
            counts[DISPOSITIONS[disposition]] += 1
            line = int(row["source_line"])
            if line in seen_lines or row["source_file"] != "sales.csv":
                raise ValueError("Duplicate source line or wrong source file")
            seen_lines.add(line)
            if disposition == "invalid":
                reasons[row["reason_code"]] += 1
                if row["row_sha256"] or row["key_sha256"]:
                    raise ValueError("Invalid row audit contains unexpected hashes")
    counts["input_rows"] = len(seen_lines)
    if seen_lines != set(range(2, 100_002)):
        raise ValueError("Missing or unexpected audit source lines")
    for name, expected in EXPECTED.items():
        if counts[name] != expected or quality[name] != expected:
            raise ValueError(f"Reconciliation mismatch: {name}")
    if dict(reasons) != quality["invalid_reasons"]:
        raise ValueError("Invalid reason distribution mismatch")
    if run["quality"] != quality or run["initial_inserted"] != 94_618:
        raise ValueError("Run summary mismatch")
    if run["replay_inserted"] != 0 or run["persisted_sales"] != 94_618:
        raise ValueError("Replay or fact count mismatch")
    if run["branches_reported"] != 5:
        raise ValueError("Unexpected branch count")
    with (reports / "sales_by_branch.csv").open(encoding="utf-8", newline="") as file:
        branches = list(csv.DictReader(file))
    if len(branches) != 5 or len({row["branch_id"] for row in branches}) != 5:
        raise ValueError("Branch report cardinality mismatch")
    if sum(int(row["unique_sales"]) for row in branches) != 94_618:
        raise ValueError("Branch sales mismatch")
    for row in branches:
        count = int(row["unique_sales"])
        revenue = Decimal(row["revenue_brl"])
        if revenue < 0:
            raise ValueError("Negative branch revenue")
        if count == 0 and row["average_ticket_brl"]:
            raise ValueError("Unexpected ticket for empty branch")
        if count > 0 and not row["average_ticket_brl"]:
            raise ValueError("Missing average ticket")
    return {"verified": True, "input_rows": counts["input_rows"],
            "accepted": counts["accepted"], "branches": len(branches)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.reports), sort_keys=True))


if __name__ == "__main__":
    main()
