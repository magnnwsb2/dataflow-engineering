# NexaRetail — verified end-to-end execution

## Evidence

- Workflow: **NexaRetail end-to-end #2**
- Branch: `main`
- Commit: `e7f7931`
- GitHub Actions conclusion: **Success**
- Duration: **2m 07s** (overall workflow)
- Artifact: `nexaretail-reports` (ZIP; 14-day retention)
- Verification: the artifact files were inspected and reconciled on 2026-10-24.
- [Open workflow history](https://github.com/magnnwsb2/dataflow-engineering/actions/workflows/pipeline.yml)

These are observed results from a **synthetic, single-run acceptance scenario**, not production performance or availability metrics.

## Data quality — observed

| Classification | Rows |
| --- | ---: |
| Input | 100,000 |
| Accepted unique | 94,618 |
| Exact duplicates | 3,006 |
| Invalid | 1,176 |
| Conflicting | 1,200 |

Invalid reasons: `INVALID_DATE=200`, `INVALID_MONEY=200`,
`INVALID_QUANTITY=150`, `MISSING_REQUIRED=176`,
`TOTAL_MISMATCH=150`, `UNKNOWN_BRANCH=150`, `UNKNOWN_PRODUCT=150`.

The `row_audit.csv` artifact has 100,000 source rows with distinct source
line numbers 2–100001; the four dispositions reconcile with the summary.

## PostgreSQL and idempotency — observed

- First load inserted: **94,618**.
- Same-run replay inserted: **0**.
- Persisted `fact_sale` rows: **94,618**.
- Branches reported: **5**.

## Gold analytics — observed

| Branch | Sales | Revenue (BRL) | Average ticket (BRL) |
| --- | ---: | ---: | ---: |
| F001 | 18,924 | 106,625,921.68 | 5,634.43 |
| F002 | 18,924 | 106,569,716.22 | 5,631.46 |
| F003 | 18,924 | 105,717,955.14 | 5,586.45 |
| F004 | 18,923 | 106,725,190.29 | 5,639.97 |
| F005 | 18,923 | 106,435,309.87 | 5,624.65 |
| **Total** | **94,618** | **532,074,093.20** | **5,623.39** |

The consolidated ticket is total revenue divided by total accepted sales,
not an unweighted average of branch ticket values.

## Tests and remaining scope

The uploaded `unit-tests.xml` reports **11 tests, 0 failures, 0 errors,
0 skipped**. The end-to-end workflow also completed its independent report
verification successfully.

The separate `PostgreSQL integration` workflow has **not** been verified
as passing. This acceptance result does not establish multi-run persistence,
production-scale throughput, or security certification.

The source dataset is entirely fictional; revenue is synthetic and must not
be represented as real company financial performance.
