"""Atomic and idempotent PostgreSQL load of validated sales."""

import csv
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from dataflow.quality.classify import SALES_COLUMNS, _references, normalize


def load(directory: Path, connection, batch_size: int = 1000) -> dict:
    """Load accepted rows; reject conflicting existing business keys."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    directory = Path(directory)
    branches = _references(directory / "branches.csv", "branch_id", ("branch_id", "branch_name", "state"))
    products = _references(directory / "products.csv", "product_id", ("product_id", "product_name", "category"))
    groups = defaultdict(Counter)
    reasons = Counter()
    input_rows = 0
    with (directory / "sales.csv").open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != SALES_COLUMNS:
            raise ValueError("Invalid sales header")
        for row in reader:
            input_rows += 1
            try:
                if None in row:
                    raise ValueError("INVALID_TYPE")
                canonical = normalize(row, branches, products)
            except ValueError as error:
                reasons[str(error)] += 1
                continue
            groups[canonical[:2]][canonical] += 1

    accepted = []
    duplicates = conflicts = 0
    for variants in groups.values():
        if len(variants) > 1:
            conflicts += sum(variants.values())
        else:
            canonical, count = next(iter(variants.items()))
            accepted.append(canonical)
            duplicates += count - 1
    summary = dict(input_rows=input_rows, accepted=len(accepted), duplicates=duplicates,
                   invalid=sum(reasons.values()), conflicts=conflicts)
    assert input_rows == sum(summary[key] for key in ("accepted", "duplicates", "invalid", "conflicts"))

    with connection.transaction():
        with connection.cursor() as cursor:
            for filename, fields, table in (
                ("branches.csv", ("branch_id", "branch_name", "state"), "dim_branch"),
                ("products.csv", ("product_id", "product_name", "category"), "dim_product"),
            ):
                with (directory / filename).open(encoding="utf-8-sig", newline="") as file:
                    reader = csv.DictReader(file)
                    if tuple(reader.fieldnames or ()) != fields:
                        raise ValueError("Invalid reference header")
                    for row in reader:
                        placeholders = ",".join(["%s"] * len(fields))
                        columns = ",".join(fields)
                        cursor.execute(
                            f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                            tuple(row[field] for field in fields),
                        )
            inserted = 0
            for canonical in accepted:
                values = (canonical[0], canonical[1], canonical[2], date.fromisoformat(canonical[3]),
                          int(canonical[4]), Decimal(canonical[5]), Decimal(canonical[6]))
                cursor.execute(
                    "INSERT INTO fact_sale (branch_id,sale_id,product_id,sale_date,quantity,unit_price,total_amount) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (branch_id,sale_id) DO NOTHING RETURNING 1",
                    values,
                )
                if cursor.fetchone():
                    inserted += 1
                else:
                    cursor.execute(
                        "SELECT product_id,sale_date,quantity,unit_price,total_amount "
                        "FROM fact_sale WHERE branch_id=%s AND sale_id=%s FOR UPDATE",
                        values[:2],
                    )
                    existing = cursor.fetchone()
                    if existing is None or tuple(existing) != values[2:]:
                        raise ValueError("Existing sale key has a conflicting payload")
    return {**summary, "inserted": inserted}
