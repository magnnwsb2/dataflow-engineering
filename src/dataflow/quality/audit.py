"""Deterministic row-level audit for NexaRetail sales.

Two-pass classification preserves CSV source line numbers, avoids retaining raw
input rows in memory, and rejects all variants of conflicting business keys.
Only sanitized metadata is exported.
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from dataflow.quality.classify import SALES_COLUMNS, _references, normalize


def _fingerprint(canonical: tuple[str, ...]) -> str:
    payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scan(source: Path, branches: set[str], products: set[str]):
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != SALES_COLUMNS:
            raise ValueError("Invalid sales header")
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                yield line_number, None, "INVALID_TYPE"
                continue
            try:
                canonical = normalize(row, branches, products)
            except ValueError as error:
                yield line_number, None, str(error)
                continue
            yield line_number, canonical, None


def audit(directory: Path, output_path: Path) -> dict:
    """Write one audit record per source row, returning reconciled totals.

    Rejected rows expose only source line, business-key hash where available,
    normalized-row hash for valid rows, disposition and reason. No raw payload.
    """
    directory = Path(directory)
    source = directory / "sales.csv"
    branches = _references(
        directory / "branches.csv", "branch_id",
        ("branch_id", "branch_name", "state"),
    )
    products = _references(
        directory / "products.csv", "product_id",
        ("product_id", "product_name", "category"),
    )

    groups: dict[tuple[str, str], Counter[tuple[str, ...]]] = defaultdict(Counter)
    for _, canonical, reason in _scan(source, branches, products):
        if reason is None:
            assert canonical is not None
            groups[canonical[:2]][canonical] += 1

    seen: Counter[tuple[str, ...]] = Counter()
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_file", "source_line", "key_sha256", "row_sha256",
                "disposition", "reason_code",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for line_number, canonical, reason in _scan(source, branches, products):
            key_hash = row_hash = ""
            if reason is not None:
                disposition = "invalid"
                reasons[reason] += 1
            else:
                assert canonical is not None
                key_hash = _fingerprint(canonical[:2])
                row_hash = _fingerprint(canonical)
                variants = groups[canonical[:2]]
                if len(variants) > 1:
                    disposition = "conflict"
                    reason = "CONFLICTING_KEY"
                elif seen[canonical]:
                    disposition = "duplicate"
                    reason = "EXACT_DUPLICATE"
                else:
                    disposition = "accepted"
                    reason = ""
                seen[canonical] += 1
            counts[disposition] += 1
            writer.writerow({
                "source_file": source.name,
                "source_line": line_number,
                "key_sha256": key_hash,
                "row_sha256": row_hash,
                "disposition": disposition,
                "reason_code": reason,
            })

    summary = {
        "input_rows": sum(counts.values()),
        "accepted": counts["accepted"],
        "duplicates": counts["duplicate"],
        "invalid": counts["invalid"],
        "conflicts": counts["conflict"],
        "invalid_reasons": dict(sorted(reasons.items())),
    }
    assert summary["input_rows"] == sum(
        summary[key] for key in ("accepted", "duplicates", "invalid", "conflicts")
    )
    return summary
