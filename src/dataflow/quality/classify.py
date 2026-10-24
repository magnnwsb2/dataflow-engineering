"""Validate and classify synthetic NexaRetail sales (RF-002–005).

Every physical input row receives exactly one disposition. Duplicate and
conflict classification is independent of input order; invalid records are
classified before key grouping. No database is used at this stage.
"""

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

SALES_COLUMNS = (
    "branch_id", "sale_id", "product_id", "sale_date",
    "quantity", "unit_price", "total_amount",
)
MONEY = re.compile(r"^[0-9]+[.,][0-9]{2}$")
BRANCH = re.compile(r"^F[0-9]{3}$")
PRODUCT = re.compile(r"^P[0-9]{4}$")
SALE = re.compile(r"^V[0-9]{8}$")


@dataclass(frozen=True)
class Result:
    input_rows: int
    accepted: int
    duplicates: int
    invalid: int
    conflicts: int
    reasons: dict[str, int]

    def assert_reconciled(self) -> None:
        assert self.input_rows == (
            self.accepted + self.duplicates + self.invalid + self.conflicts
        )


def _money(value: str) -> Decimal:
    if not MONEY.fullmatch(value):
        raise ValueError("INVALID_MONEY")
    amount = Decimal(value.replace(",", "."))
    if amount <= 0:
        raise ValueError("INVALID_MONEY")
    return amount


def _date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("INVALID_DATE")


def normalize(row: dict[str, str], branches: set[str], products: set[str]) -> tuple[str, ...]:
    if any(row.get(field) is None or not row[field].strip() for field in SALES_COLUMNS):
        raise ValueError("MISSING_REQUIRED")
    branch, sale, product = (row["branch_id"].strip(), row["sale_id"].strip(), row["product_id"].strip())
    if not BRANCH.fullmatch(branch) or not SALE.fullmatch(sale) or not PRODUCT.fullmatch(product):
        raise ValueError("INVALID_TYPE")
    if branch not in branches:
        raise ValueError("UNKNOWN_BRANCH")
    if product not in products:
        raise ValueError("UNKNOWN_PRODUCT")
    when = _date(row["sale_date"].strip())
    quantity_text = row["quantity"].strip()
    if not quantity_text.isascii() or not quantity_text.isdecimal():
        raise ValueError("INVALID_QUANTITY")
    quantity = int(quantity_text)
    if not 1 <= quantity <= 1000:
        raise ValueError("INVALID_QUANTITY")
    try:
        price = _money(row["unit_price"].strip())
        total = _money(row["total_amount"].strip())
    except (InvalidOperation, ValueError):
        raise ValueError("INVALID_MONEY") from None
    if total != price * quantity:
        raise ValueError("TOTAL_MISMATCH")
    return (branch, sale, product, when, str(quantity), f"{price:.2f}", f"{total:.2f}")


def _references(path: Path, key: str, required: tuple[str, ...]) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != set(required):
            raise ValueError(f"Invalid reference header: {path.name}")
        result: set[str] = set()
        for row in reader:
            if None in row or any(not row.get(field) or not row[field].strip() for field in required):
                raise ValueError(f"Invalid reference row: {path.name}")
            identifier = row[key].strip()
            if identifier in result:
                raise ValueError(f"Duplicate reference: {identifier}")
            result.add(identifier)
        return result


def classify(directory: Path) -> Result:
    directory = Path(directory)
    branches = _references(directory / "branches.csv", "branch_id", ("branch_id", "branch_name", "state"))
    products = _references(directory / "products.csv", "product_id", ("product_id", "product_name", "category"))
    groups: dict[tuple[str, str], dict[tuple[str, ...], int]] = defaultdict(lambda: defaultdict(int))
    reasons: dict[str, int] = defaultdict(int)
    input_rows = 0
    with (directory / "sales.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != SALES_COLUMNS:
            raise ValueError("Invalid sales header")
        for row in reader:
            input_rows += 1
            if None in row:
                reasons["INVALID_TYPE"] += 1
                continue
            try:
                canonical = normalize(row, branches, products)
            except ValueError as exc:
                reasons[str(exc)] += 1
                continue
            groups[canonical[:2]][canonical] += 1

    accepted = duplicates = conflicts = 0
    for variants in groups.values():
        if len(variants) > 1:
            conflicts += sum(variants.values())
        else:
            count = next(iter(variants.values()))
            accepted += 1
            duplicates += count - 1
    result = Result(input_rows, accepted, duplicates, sum(reasons.values()), conflicts, dict(reasons))
    result.assert_reconciled()
    return result
