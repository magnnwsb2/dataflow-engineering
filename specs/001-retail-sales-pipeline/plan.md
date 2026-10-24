# Technical Implementation Plan — NexaRetail Retail Sales Pipeline

**Feature:** 001-retail-sales-pipeline  
**Version:** 0.2.0  
**Status:** Business scope and 100,000-row distribution approved; technical security verification pending  
**Target scale:** 100,000 synthetic sales input rows  
**Constitution:** [../../.specify/memory/constitution.md](../../.specify/memory/constitution.md)  
**Specification:** [spec.md](spec.md)

## 1. Summary and scope

Design a deterministic batch data engineering pipeline for five fictional retail branches and 200 fictional products. Generate exactly 100,000 sales CSV *input rows*, including controlled anomalies; ingest, validate, normalize, deduplicate, load valid records into ephemeral PostgreSQL, and publish quality evidence and branch-level analytics as GitHub Actions artifacts. The approved distribution is **94,618 accepted unique, 3,006 exact duplicates, 1,176 invalid, and 1,200 conflicting input rows** (600 two-row conflict groups); total **100,000**. These are acceptance targets, not observed pipeline outputs. See [data-manifest.md](data-manifest.md).

No implementation code or workflow YAML is included in this planning document.

## 2. Architectural constraints

- GitHub-hosted Actions runners only; no self-hosted infrastructure or third-party cloud/data APIs.
- PostgreSQL runs as an ephemeral service container within a single job. It is discarded after the job.
- Runtime configuration via environment variables; use GitHub Secrets for any real secret. Never commit populated .env files, credentials, or tokens.
- Generated synthetic input, intermediate data, reports, and test results are ephemeral or stored as sanitized Actions artifacts, not committed automatically.
- Package installation from registries is allowed by the constitution; dependency versions and action references must be pinned and reviewed before implementation.
- No Airflow, Kafka, Spark, public API, or persistent DB for the MVP.
- Use a least-privilege workflow token (`contents: read` for read-only workflows), concurrency controls as appropriate, and an explicit artifact retention policy.

## 3. Logical architecture

1. **Generator:** deterministic synthetic reference and sales CSVs, including reproducible anomalies.
2. **Bronze:** immutable-in-run raw CSV input and metadata (source file, row number, checksum, run ID); no permanent external raw store.
3. **Silver:** schema checks, parsing, normalization, referential validation, duplicate/conflict resolution, rejection classification.
4. **Load:** transactionally insert normalized dimensions and fact rows into PostgreSQL, using stable business keys and conflict-safe idempotent operations.
5. **Gold:** SQL aggregates per branch (revenue, unique sales, average ticket), including branches with zero sales.
6. **Observability:** structured run summary, counts, reconciliation, sanitized diagnostics, quality reports.
7. **Delivery:** publish CSV/JSON reports and test evidence as GitHub Actions artifacts.

Bronze/Silver/Gold are logical layers in this MVP, not persistent cloud storage tiers. PostgreSQL persists only for the duration of the job.

## 4. Technology choices and justification

| Component | Choice | Rationale |
| --- | --- | --- |
| Core | Python 3.12 (proposed) | Portable, readable batch processing and deterministic fixtures |
| Parsing | Python csv + decimal + datetime | Standard library; avoids unnecessary memory-intensive dataframe dependency |
| DB | PostgreSQL 16 (proposed) | SQL constraints, transactions, service container support |
| Driver | psycopg 3 (proposed) | Parameterized SQL and transaction support |
| Tests | pytest (proposed) | Unit and integration/acceptance tests |
| Orchestration | GitHub Actions | GitHub-only ephemeral automation |
| Reports | CSV, JSON, JUnit XML | Portable, inspectable, Actions-friendly |
| Data generation | Python random with fixed seed | Reproducible fixtures without external APIs |

Pin exact supported versions/digests during implementation planning; the versions above are proposals, not verified runner availability guarantees.

## 5. Input data contracts

All CSVs: UTF-8, comma-delimited, header required, RFC 4180-style quoting, one record per line (quoted fields may contain delimiters), no real PII. Missing or extra required columns cause file-level schema failure, not silent row acceptance. Whitespace is trimmed from identifiers and names. Empty mandatory fields are invalid.

### branches.csv

| Column | Type | Constraints |
| --- | --- | --- |
| branch_id | string | Required; pattern `F[0-9]{3}`; unique |
| branch_name | string | Required; 1–100 characters |
| state | string | Required; two uppercase letters |

Generate exactly 5 distinct branches, `F001` through `F005`.

### products.csv

| Column | Type | Constraints |
| --- | --- | --- |
| product_id | string | Required; pattern `P[0-9]{4}`; unique |
| product_name | string | Required; 1–120 characters |
| category | string | Required; 1–60 characters |

Generate exactly 200 distinct products, `P0001` through `P0200`.

### sales.csv

| Column | Type | Constraints |
| --- | --- | --- |
| branch_id | string | Required; valid branch reference |
| sale_id | string | Required; pattern `V[0-9]{8}`; unique within branch |
| product_id | string | Required; valid product reference |
| sale_date | string | Required; `YYYY-MM-DD` or `DD/MM/YYYY` |
| quantity | integer | Required; 1–1000 |
| unit_price | decimal | Required; positive BRL amount, 2 decimal places |
| total_amount | decimal | Required; positive BRL amount, 2 decimal places; must equal quantity × unit_price |

**Money formats:** accept `1234.56` and `1234,56` (no thousands separators); reject mixed locale/thousands formats such as `1.234,56` or `1,234.56`. Normalize to decimal with two fractional digits. Use Decimal and PostgreSQL NUMERIC; never floating-point for money.

**Date formats:** `YYYY-MM-DD` and `DD/MM/YYYY` only, both parsed strictly and normalized to ISO date. Reject impossible dates and ambiguous formats not in the allowlist.

**Row grain:** one sale = one product transaction, not an invoice with multiple items. Each valid row must satisfy `total_amount = quantity * unit_price` exactly at two-decimal precision. Discounts, returns, taxes, and refunds are out of scope.

**Synthetic dataset:** 100,000 sales input rows across five branches, with fixed seed (proposed `20271024`) and an explicit generator version. The approved anomaly mix is fixed in [data-manifest.md](data-manifest.md): 94,618 accepted, 3,006 duplicates, 1,176 invalid, and 1,200 conflicts. Test exact counts against the generated fixture manifest. Do not assert 100,000 accepted sales.

## 6. Proposed PostgreSQL model

### dim_branch
- `branch_id VARCHAR(4) PRIMARY KEY`
- `branch_name VARCHAR(100) NOT NULL`
- `state CHAR(2) NOT NULL`

### dim_product
- `product_id VARCHAR(5) PRIMARY KEY`
- `product_name VARCHAR(120) NOT NULL`
- `category VARCHAR(60) NOT NULL`

### fact_sale
- `branch_id VARCHAR(4) NOT NULL REFERENCES dim_branch(branch_id)`
- `sale_id VARCHAR(9) NOT NULL`
- `product_id VARCHAR(5) NOT NULL REFERENCES dim_product(product_id)`
- `sale_date DATE NOT NULL`
- `quantity INTEGER NOT NULL CHECK (quantity > 0)`
- `unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price > 0)`
- `total_amount NUMERIC(16,2) NOT NULL CHECK (total_amount > 0)`
- `PRIMARY KEY (branch_id, sale_id)`
- `CHECK (total_amount = quantity * unit_price)`

### pipeline_run
- `run_id TEXT PRIMARY KEY`
- `started_at TIMESTAMPTZ NOT NULL`
- `finished_at TIMESTAMPTZ NULL`
- `status TEXT NOT NULL`
- `input_count INTEGER NOT NULL DEFAULT 0`
- `accepted_count INTEGER NOT NULL DEFAULT 0`
- `invalid_count INTEGER NOT NULL DEFAULT 0`
- `duplicate_count INTEGER NOT NULL DEFAULT 0`
- `conflict_count INTEGER NOT NULL DEFAULT 0`

### rejected_row
- `run_id TEXT NOT NULL REFERENCES pipeline_run(run_id)`
- `source_file TEXT NOT NULL`
- `source_row INTEGER NOT NULL`
- `reason_code TEXT NOT NULL`
- `source_fingerprint TEXT NOT NULL`
- `PRIMARY KEY (run_id, source_file, source_row, reason_code)`

The rejection table stores references/fingerprints, not raw potentially sensitive row payloads. For the MVP, reference CSVs must be valid or fail the batch before loading; row-level rejection applies to sales. This avoids silent cascading dimension errors.

## 7. Data quality and duplicate policy

1. Validate CSV headers and reference tables first. A reference schema/uniqueness error fails the run.
2. Parse sales rows; malformed rows receive a stable reason code and source position.
3. Normalize valid rows before calculating a canonical fingerprint.
4. Group all structurally valid rows by `(branch_id, sale_id)` **before selecting accepted rows**.
5. If a group contains more than one distinct normalized payload, reject **every row in that group** as `CONFLICTING_SALE_KEY`. Do not arbitrarily keep a winner.
6. Otherwise retain one canonical row and classify extra occurrences as `EXACT_DUPLICATE`. The retained row must still pass referential and business checks.
7. Reject unknown branch/product references; never insert invalid rows into `fact_sale`.
8. Maintain mutually exclusive row dispositions: accepted, invalid, duplicate, or conflict. For each run: `input = accepted + invalid + duplicate + conflict` for the first load. On rerun, accepted refers to logically valid unique records, not newly inserted rows; separately report `inserted_count` and `already_present_count`.
9. On idempotent rerun, compare full normalized payload for existing keys; a divergent payload fails with an explicit cross-batch conflict instead of silently ignoring it.

**Proposed reason codes:** `MISSING_REQUIRED`, `INVALID_TYPE`, `INVALID_DATE`, `INVALID_MONEY`, `INVALID_QUANTITY`, `TOTAL_MISMATCH`, `UNKNOWN_BRANCH`, `UNKNOWN_PRODUCT`, `EXACT_DUPLICATE`, `CONFLICTING_SALE_KEY`. Conflict and duplicate categories are reported separately from invalid records; reports include all nonaccepted rows with their disposition.

## 8. Transactionality and failure recovery

- Establish schema and dimensions in deterministic initialization steps.
- Validate and classify the batch before loading facts.
- Insert facts and update run metadata inside explicit transactions with rollback on failure.
- Test injected failure *after a subset of inserts but before commit*; the transaction must roll back fully.
- Retry the same batch within the same job and DB; verify expected counts, unique keys, and revenue reconciliation.
- A run failure must be visible in workflow status, and sanitized diagnostics must still be uploaded using a conditional artifact step.
- An independent new GitHub Actions run starts with a fresh DB, not a resumed DB state.

## 9. Gold analytics and reconciliation

For each of the five branches, including those with no accepted sales:
- `revenue_brl = SUM(total_amount)`, default 0.00;
- `unique_sales = COUNT(*)` over accepted unique fact rows;
- `average_ticket_brl = revenue_brl / unique_sales`, or null when count is zero, rounded to two decimals for reporting;
- a run summary with accepted, invalid, duplicate, conflict, inserted, and already-present counts.

Check: total Gold revenue equals sum of fact amounts; sum of branch counts equals total fact rows; disposition totals equal source sales row count.

## 10. Test strategy and traceability

| Test class | Scenario | Requirements / criteria |
| --- | --- | --- |
| Unit | Date and monetary parsing, required fields, total mismatch | RF-002/003, RN-003/004 |
| Unit | Canonical keys, exact duplicates, conflict groups | RF-004/005, CA-002/007 |
| Unit | Rejection codes and row-count reconciliation | RF-005/008, CA-003 |
| Integration | Dimension foreign keys and valid 100-row batch | RF-001/006, CA-001/008 |
| Integration | Re-run same batch against same PostgreSQL instance | RF-009, CA-004 |
| Integration | Inject pre-commit failure and retry | RF-006/009, CA-005 |
| Integration | Branch aggregation and revenue reconciliation | RF-007, CA-009 |
| CI acceptance | Artifacts, least privilege, secret scanning/checks | RF-010, CA-006/010 |
| End-to-end | 100,000 deterministic sales input rows and manifest reconciliation | RF-001–010 |

Tests must fail the job on violations. Unit tests can run without PostgreSQL; integration and end-to-end tests use the Actions service container. Performance measurements are informative, not production claims.

## 11. GitHub Actions design (planned, not implemented)

### ci.yml
Triggers: pull_request and push to main. Read-only repository permissions. Steps: checkout at pinned action ref, setup Python at pinned action ref, install pinned dependencies, run unit tests, run integration tests with PostgreSQL service container, export JUnit XML and sanitized test summary, upload artifacts even on test failure. Set timeouts and artifact retention.

### pipeline.yml
Triggers: workflow_dispatch (manual) and optionally a scheduled trigger **only after approval**. Single job with PostgreSQL service container; generate 100,000 synthetic rows, initialize schema, process Bronze/Silver/Gold, run reconciliation and idempotency checks, write quality metrics, and upload sanitized reports. A separate intentional-failure test path exercises rollback/retry without masking real failures. No repository writes or persistent DB.

### Configuration contract
Environment variables (names proposed): `DATASET_SEED`, `SALES_ROW_COUNT`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `OUTPUT_DIR`, `RUN_ID`. Do not hardcode credentials in Python or workflow source. For ephemeral CI credentials, inject a per-job generated password into both service and client where supported; otherwise use a documented isolated non-production service secret managed in GitHub Actions secrets. Do not echo secrets.

### Artifacts
- `sales_by_branch.csv`
- `quality_summary.json`
- `rejections.csv` (sanitized: file, row, disposition, reason, fingerprint)
- `run_summary.json`
- `test-results.xml`

Suggested retention: 14 days (subject to repository/org GitHub policy). No generated business datasets committed to git.

## 12. Planned repository layout

```text
.github/workflows/ci.yml
.github/workflows/pipeline.yml
.specify/memory/constitution.md
specs/001-retail-sales-pipeline/spec.md
specs/001-retail-sales-pipeline/plan.md
specs/001-retail-sales-pipeline/tasks.md
src/dataflow/generation/
src/dataflow/ingestion/
src/dataflow/quality/
src/dataflow/transformation/
src/dataflow/storage/
src/dataflow/reporting/
tests/unit/
tests/integration/
tests/acceptance/
data/sample/
docs/
.env.example
README.md
.gitignore
```

Only `plan.md` is being created at this stage; paths above are proposed future deliverables.

## 13. Risks and trade-offs

- **100k rows on hosted runners:** stream or process in bounded batches; do not load unbounded dataframes unnecessarily. Benchmark after implementation.
- **Ephemeral DB:** no cross-run database history; reproducibility and within-run retries demonstrate correctness, not long-term state management.
- **Artifact retention:** reports expire; keep specs, fixture manifest, and generation parameters versioned.
- **GitHub-only restriction:** avoid external APIs and hosting; package installation and GitHub-hosted compute are explicit allowed dependencies.
- **Conflicting sale keys:** rejecting all conflicting versions favors correctness over completeness; measure and report data loss.
- **Security:** Actions secrets may require manual repository setup; do not assume they are configured.

## 14. Decision log and pending approvals

**Approved:** fictional retail domain, GitHub-only hosted execution, ephemeral PostgreSQL, Actions artifacts, environment-variable configuration, 100,000 synthetic sales input rows, the precise approved category counts (94,618 / 3,006 / 1,176 / 1,200), specification-first development.

**Proposed in this plan:** five branches, 200 products, Python 3.12, PostgreSQL 16, psycopg 3, standard-library CSV/Decimal, two allowed date formats, two allowed monetary formats, 14-day artifact retention, fixed generator seed 20271024, conflict-group rejection, manual pipeline dispatch as default.

**Before coding:** tasks.md exists and the category-count manifest is approved; complete the security feasibility check for PostgreSQL service authentication, pin dependency versions and workflow actions, and verify remaining technical assumptions. Generated data and tests have not yet been executed.

## 15. Exit criteria for planning

The plan is reviewable, consistent with the constitution and spec, and every functional requirement has a proposed implementation responsibility and test. The next SDD step is `tasks.md`, not coding.
