"""Live PostgreSQL integrity tests using the ephemeral Actions service."""

from decimal import Decimal

import pytest

from dataflow.storage.connection import connect_from_env
from dataflow.storage.schema import apply_schema


@pytest.fixture
def db():
    with connect_from_env() as connection:
        apply_schema(connection)
        with connection.transaction():
            connection.execute("TRUNCATE fact_sale, rejected_row, pipeline_run, dim_product, dim_branch CASCADE")
        yield connection


def test_schema_and_constraints(db):
    with db.transaction():
        db.execute(
            "INSERT INTO dim_branch (branch_id, branch_name, state) "
            "VALUES (%s, %s, %s)",
            ("F001", "Filial Teste", "PE"),
        )
        db.execute(
            "INSERT INTO dim_product (product_id, product_name, category) "
            "VALUES (%s, %s, %s)",
            ("P0001", "Produto Teste", "Casa"),
        )
        db.execute(
            "INSERT INTO fact_sale "
            "(branch_id, sale_id, product_id, sale_date, quantity, unit_price, total_amount) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ("F001", "V00000001", "P0001", "2026-01-05", 2, Decimal("12.50"), Decimal("25.00")),
        )
    assert db.execute("SELECT count(*) FROM fact_sale").fetchone()[0] == 1


@pytest.mark.parametrize(
    "product,quantity,price,total",
    [
        ("P9999", 1, Decimal("12.50"), Decimal("12.50")),
        ("P0001", 0, Decimal("12.50"), Decimal("0.00")),
        ("P0001", 2, Decimal("12.50"), Decimal("25.01")),
    ],
)
def test_reject_invalid_sale(db, product, quantity, price, total):
    with db.transaction():
        db.execute(
            "INSERT INTO dim_branch (branch_id, branch_name, state) "
            "VALUES ('F001', 'Filial Teste', 'PE') ON CONFLICT DO NOTHING"
        )
        db.execute(
            "INSERT INTO dim_product (product_id, product_name, category) "
            "VALUES ('P0001', 'Produto Teste', 'Casa') ON CONFLICT DO NOTHING"
        )
    with pytest.raises(Exception):
        with db.transaction():
            db.execute(
                "INSERT INTO fact_sale "
                "(branch_id, sale_id, product_id, sale_date, quantity, unit_price, total_amount) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                ("F001", "V00000009", product, "2026-01-05", quantity, price, total),
            )
    assert db.execute(
        "SELECT count(*) FROM fact_sale WHERE sale_id = 'V00000009'"
    ).fetchone()[0] == 0
