"""Static checks of the initial versioned SQL schema.

These do not replace real PostgreSQL integration tests.
"""

from dataflow.storage.schema import schema_sql


def test_required_tables_and_constraints_are_declared() -> None:
    sql = schema_sql()
    for table in ("dim_branch", "dim_product", "fact_sale", "pipeline_run", "rejected_row"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "PRIMARY KEY (branch_id, sale_id)" in sql
    assert "REFERENCES dim_branch(branch_id)" in sql
    assert "REFERENCES dim_product(product_id)" in sql
    assert "CHECK (total_amount = quantity * unit_price)" in sql
    assert "REFERENCES pipeline_run(run_id)" in sql
