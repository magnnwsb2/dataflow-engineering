# DataFlow Engineering

**Spec-driven data engineering portfolio · NexaRetail (fictional)**

An end-to-end Python and PostgreSQL retail sales pipeline designed for **reproducibility, data quality, auditability, transactional integrity, and idempotent processing**. All business data is synthetic.

> **Verification status:** implementation and tests are committed; a successful PostgreSQL-backed GitHub Actions run has **not yet been verified**. The quantities below are acceptance targets, not measured production results.

## Architecture

```text
Deterministic generator (Python, CSV)
        |
        v
Bronze: 100,000 synthetic sales input rows
        |
        v
Silver: normalize / validate / deduplicate / reject conflicts
        |                                |
        v                                v
PostgreSQL 16                       Row audit (CSV)
dim_branch / dim_product                 |
fact_sale (business-key PK)              v
        |                          Quality summary (JSON)
        v
Gold: sales by branch (CSV)
        |
        v
GitHub Actions artifacts + execution summary (JSON)
```

PostgreSQL is an **ephemeral GitHub Actions service**, not an external managed database. The pipeline also performs a same-run replay to check idempotency.

## Data contract

| Sales disposition | Expected rows |
| --- | ---: |
| Accepted unique | 94,618 |
| Exact duplicates | 3,006 |
| Invalid | 1,176 |
| Conflicting (both variants rejected) | 1,200 |
| **Total input** | **100,000** |

Five fictional branches (`F001`–`F005`), 200 fictional products (`P0001`–`P0200`), fixed generator seed `20271024`. Monetary amounts are handled using Python `Decimal` and PostgreSQL `NUMERIC`, not floating-point arithmetic. A sale is uniquely identified by `(branch_id, sale_id)`.

The intended database result is **94,618 fact rows on first load and zero additional rows on replay**. Actual results must be verified through a successful workflow run.

## Implemented components

- **Generation:** `src/dataflow/generation/synthetic.py` — deterministic CSVs and manifest with SHA-256 hashes.
- **Quality:** `src/dataflow/quality/classify.py` and `audit.py` — row validation, classification and sanitized source-line audit.
- **Storage:** `sql/001_initial_schema.sql` and `src/dataflow/storage/` — PostgreSQL schema, environment-based connection, transactional insert/replay.
- **Analytics:** `src/dataflow/analytics/report.py` — per-branch sales count, BRL revenue and average ticket.
- **Orchestration:** `src/dataflow/pipeline.py` and `src/dataflow/__main__.py`.
- **Tests:** `tests/unit/` and `tests/integration/`.
- **CI:** `.github/workflows/ci.yml`, `postgres-integration.yml` and `pipeline.yml`.

## How to run

Python 3.12 and access to PostgreSQL 16 are required for the full pipeline.

```bash
python -m pip install -e '.[test,postgres]'
python -m pytest tests/unit -v
python -m dataflow --workdir ./artifacts
```

The database connection uses `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD` environment variables. Never commit a populated `.env` file.

**GitHub-hosted run:** set the repository Actions secret `CI_POSTGRES_PASSWORD`, then manually dispatch **NexaRetail end-to-end** from the Actions tab. The workflow provisions a temporary PostgreSQL service and publishes sanitized reports. The secret must be created by the repository owner and should never be shared in chat.

See [Execution and verification runbook](docs/runbook.md).

## Expected artifacts

| Artifact | Purpose |
| --- | --- |
| `row_audit.csv` | One sanitized audit record per input row |
| `quality_summary.json` | Counts and reasons for rejected sales |
| `sales_by_branch.csv` | Gold business metrics for five branches |
| `run_summary.json` | Load, replay, persisted count and manifest hashes |

GitHub Actions artifacts have a configured retention of 14 days.

## Engineering decisions

- **No real personal or customer data:** NexaRetail and all sales are fictional.
- **No secrets in source:** use repository Actions secrets and environment variables.
- **No external data platform:** execution stays within GitHub-hosted runners.
- **Fail closed on conflicts:** mismatching payloads with an existing sale key abort the transaction.
- **Traceability:** [constitution](.specify/memory/constitution.md), [requirements](specs/001-retail-sales-pipeline/spec.md), [technical plan](specs/001-retail-sales-pipeline/plan.md), [task breakdown](specs/001-retail-sales-pipeline/tasks.md), [data manifest](specs/001-retail-sales-pipeline/data-manifest.md) and [security ADR](docs/adr/001-github-actions-postgres-security.md).

## Validation and project status

The repository contains executable code and tests, but **passing CI and integration results are still pending confirmation**. This README deliberately does not claim measured throughput, reliability, or a successful 100,000-row database load.

The next milestone is a successful PostgreSQL integration and end-to-end workflow run, followed by inspection of its generated artifacts.
