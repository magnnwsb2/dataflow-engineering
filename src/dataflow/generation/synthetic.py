"""Deterministic NexaRetail synthetic CSV generator (RF-001).

Generation is not an ETL run: quality classification and PostgreSQL loading
are separate, later tasks. The output manifest records expected counts.
"""

import csv
import hashlib
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 20271024
VALID = 94_618
DUPLICATES = 3_006
INVALID = 1_176
CONFLICT = 1_200
INVALID_REASONS = {
    "MISSING_REQUIRED": 176,
    "INVALID_DATE": 200,
    "INVALID_MONEY": 200,
    "INVALID_QUANTITY": 150,
    "TOTAL_MISMATCH": 150,
    "UNKNOWN_BRANCH": 150,
    "UNKNOWN_PRODUCT": 150,
}
SALES_FIELDS = [
    "branch_id", "sale_id", "product_id", "sale_date",
    "quantity", "unit_price", "total_amount",
]


def _sale(index: int, rng: random.Random) -> dict[str, str]:
    quantity = rng.randint(1, 8)
    cents = rng.randint(150, 250_000)
    price = Decimal(cents) / 100
    return {
        "branch_id": f"F{index % 5 + 1:03d}",
        "sale_id": f"V{index + 1:08d}",
        "product_id": f"P{rng.randint(1, 200):04d}",
        "sale_date": (date(2026, 1, 1) + timedelta(days=rng.randint(0, 364))).isoformat(),
        "quantity": str(quantity),
        "unit_price": f"{price:.2f}",
        "total_amount": f"{price * quantity:.2f}",
    }


def _invalid(row: dict[str, str], reason: str) -> None:
    if reason == "MISSING_REQUIRED":
        row["product_id"] = ""
    elif reason == "INVALID_DATE":
        row["sale_date"] = "2026-02-30"
    elif reason == "INVALID_MONEY":
        row["unit_price"] = "not-money"
    elif reason == "INVALID_QUANTITY":
        row["quantity"] = "0"
    elif reason == "TOTAL_MISMATCH":
        row["total_amount"] = f"{Decimal(row['total_amount']) + Decimal('0.01'):.2f}"
    elif reason == "UNKNOWN_BRANCH":
        row["branch_id"] = "F999"
    elif reason == "UNKNOWN_PRODUCT":
        row["product_id"] = "P9999"
    else:
        raise ValueError(f"Unsupported anomaly: {reason}")


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate(output_dir: Path, seed: int = SEED) -> dict:
    """Create exactly 100,000 deterministic input sales and a summary manifest."""
    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    branches = [
        {"branch_id": f"F{i:03d}", "branch_name": f"Filial {i}", "state": state}
        for i, state in enumerate(["PE", "MA", "CE", "PB", "RN"], start=1)
    ]
    products = [
        {"product_id": f"P{i:04d}", "product_name": f"Produto {i:04d}",
         "category": ["Eletronicos", "Casa", "Moda", "Papelaria"][i % 4]}
        for i in range(1, 201)
    ]
    accepted = [_sale(i, rng) for i in range(VALID)]
    rows = [dict(row) for row in accepted]
    rows.extend(dict(row) for row in accepted[:DUPLICATES])

    next_id = VALID
    for reason, count in INVALID_REASONS.items():
        for _ in range(count):
            row = _sale(next_id, rng)
            next_id += 1
            _invalid(row, reason)
            rows.append(row)

    for _ in range(CONFLICT // 2):
        first = _sale(next_id, rng)
        next_id += 1
        second = dict(first)
        second["quantity"] = str(int(first["quantity"]) + 1)
        second["total_amount"] = f"{Decimal(first['unit_price']) * int(second['quantity']):.2f}"
        rows.extend([first, second])

    assert len(rows) == 100_000
    rng.shuffle(rows)

    paths = {
        "branches": output_dir / "branches.csv",
        "products": output_dir / "products.csv",
        "sales": output_dir / "sales.csv",
    }
    _write_csv(paths["branches"], ["branch_id", "branch_name", "state"], branches)
    _write_csv(paths["products"], ["product_id", "product_name", "category"], products)
    _write_csv(paths["sales"], SALES_FIELDS, rows)

    revenue = sum((Decimal(row["total_amount"]) for row in accepted), Decimal("0.00"))
    per_branch = {
        branch["branch_id"]: {
            "sales": sum(row["branch_id"] == branch["branch_id"] for row in accepted),
            "revenue": f"{sum((Decimal(row['total_amount']) for row in accepted if row['branch_id'] == branch['branch_id']), Decimal('0.00')):.2f}",
        }
        for branch in branches
    }
    manifest = {
        "seed": seed,
        "generator_version": "0.1.0",
        "input_sales": len(rows),
        "expected_accepted": VALID,
        "expected_duplicates": DUPLICATES,
        "expected_invalid": INVALID,
        "expected_conflicts": CONFLICT,
        "expected_conflict_groups": CONFLICT // 2,
        "invalid_reasons": INVALID_REASONS,
        "expected_revenue": f"{revenue:.2f}",
        "per_branch": per_branch,
        "sha256": {name: _sha256(path) for name, path in paths.items()},
    }
    (output_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
