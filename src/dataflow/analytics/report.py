"""Export branch-level Gold metrics from PostgreSQL as a deterministic CSV."""

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


QUERY = """
SELECT b.branch_id, b.branch_name,
       COUNT(s.sale_id)::BIGINT AS unique_sales,
       COALESCE(SUM(s.total_amount), 0)::NUMERIC(18,2) AS revenue_brl
FROM dim_branch AS b
LEFT JOIN fact_sale AS s ON s.branch_id = b.branch_id
GROUP BY b.branch_id, b.branch_name
ORDER BY b.branch_id
"""

COLUMNS = ("branch_id", "branch_name", "unique_sales", "revenue_brl", "average_ticket_brl")


def branch_report(connection, destination: Path) -> list[dict[str, str]]:
    """Write one row per branch, including branches without sales."""
    rows = connection.execute(QUERY).fetchall()
    output = []
    for branch_id, branch_name, count, revenue in rows:
        ticket = (
            (revenue / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if count else None
        )
        output.append({
            "branch_id": branch_id,
            "branch_name": branch_name,
            "unique_sales": str(count),
            "revenue_brl": f"{revenue:.2f}",
            "average_ticket_brl": f"{ticket:.2f}" if ticket is not None else "",
        })
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    return output
