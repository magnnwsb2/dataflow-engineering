"""Gold reporting test with a small controlled database fixture."""

import csv
from decimal import Decimal

from dataflow.analytics.report import branch_report
from dataflow.storage.connection import connect_from_env
from dataflow.storage.schema import apply_schema


def test_branch_report_with_zero_sales_and_exact_decimal(tmp_path):
    with connect_from_env() as db:
        apply_schema(db)
        with db.transaction():
            db.execute("TRUNCATE fact_sale, rejected_row, pipeline_run, dim_product, dim_branch CASCADE")
            db.execute(
                "INSERT INTO dim_branch (branch_id, branch_name, state) VALUES "
                "('F001', 'Filial Um', 'PE'), ('F002', 'Filial Dois', 'MA')"
            )
            db.execute(
                "INSERT INTO dim_product (product_id, product_name, category) "
                "VALUES ('P0001', 'Produto', 'Casa')"
            )
            db.execute(
                "INSERT INTO fact_sale "
                "(branch_id,sale_id,product_id,sale_date,quantity,unit_price,total_amount) "
                "VALUES ('F001','V00000001','P0001','2026-01-05',2,12.50,25.00),"
                "('F001','V00000002','P0001','2026-01-06',1,10.00,10.00)"
            )
        destination = tmp_path / "sales_by_branch.csv"
        rows = branch_report(db, destination)
        assert rows == [
            {"branch_id": "F001", "branch_name": "Filial Um", "unique_sales": "2",
             "revenue_brl": "35.00", "average_ticket_brl": "17.50"},
            {"branch_id": "F002", "branch_name": "Filial Dois", "unique_sales": "0",
             "revenue_brl": "0.00", "average_ticket_brl": ""},
        ]
        with destination.open(encoding="utf-8", newline="") as file:
            assert list(csv.DictReader(file)) == rows
