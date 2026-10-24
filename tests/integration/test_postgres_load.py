"""PostgreSQL load/replay and rollback acceptance tests."""

import pytest

from dataflow.generation.synthetic import generate
from dataflow.storage.connection import connect_from_env
from dataflow.storage.load import load
from dataflow.storage.schema import apply_schema


@pytest.fixture
def db():
    with connect_from_env() as connection:
        apply_schema(connection)
        with connection.transaction():
            connection.execute("TRUNCATE fact_sale, rejected_row, pipeline_run, dim_product, dim_branch CASCADE")
        yield connection


def test_load_and_replay_are_idempotent(db, tmp_path):
    source = tmp_path / "source"
    generate(source)
    first = load(source, db)
    assert first == {
        "input_rows": 100_000, "accepted": 94_618, "duplicates": 3_006,
        "invalid": 1_176, "conflicts": 1_200, "inserted": 94_618,
    }
    assert db.execute("SELECT count(*) FROM fact_sale").fetchone()[0] == 94_618
    second = load(source, db)
    assert second["inserted"] == 0
    assert db.execute("SELECT count(*) FROM fact_sale").fetchone()[0] == 94_618


def test_batch_failure_rolls_back_dimensions(db, tmp_path):
    source = tmp_path / "source"
    generate(source)
    with db.transaction():
        db.execute(
            "INSERT INTO dim_branch (branch_id, branch_name, state) "
            "VALUES ('F001', 'Filial Teste', 'PE')"
        )
        db.execute(
            "INSERT INTO dim_product (product_id, product_name, category) "
            "VALUES ('P0001', 'Produto Teste', 'Casa')"
        )
        db.execute(
            "INSERT INTO fact_sale "
            "(branch_id,sale_id,product_id,sale_date,quantity,unit_price,total_amount) "
            "VALUES ('F001','V00000001','P0001','2026-01-01',1,10.00,10.00)"
        )
    with pytest.raises(ValueError, match="conflicting payload"):
        load(source, db)
    assert db.execute("SELECT count(*) FROM fact_sale").fetchone()[0] == 1
    assert db.execute("SELECT count(*) FROM dim_branch").fetchone()[0] == 1
    assert db.execute("SELECT count(*) FROM dim_product").fetchone()[0] == 1
