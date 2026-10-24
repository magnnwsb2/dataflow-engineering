# Feature Specification: NexaRetail Retail Sales Data Pipeline

**Feature ID:** 001-retail-sales-pipeline  
**Version:** 0.2.0  
**Status:** Approved business scope and distribution; implementation not started  
**Project:** DataFlow Engineering  
**Method:** Spec-Driven Development (SDD)

## 1. Business context

NexaRetail is a fictional retailer with five branches. Sales, products, and branch reference records arrive in CSV files with inconsistent formatting, duplicate transactions, missing fields, invalid references, and conflicting values. Management needs trustworthy branch-level revenue and transaction indicators.

## 2. Goal

Provide a deterministic, auditable, GitHub-hosted pipeline that ingests synthetic CSV files, validates and normalizes records, loads accepted data into ephemeral PostgreSQL, and exports branch-level analytics plus quality evidence as GitHub Actions artifacts.

**Approved synthetic sales distribution:** exactly 100,000 input rows: **94,618 accepted unique**, **3,006 exact duplicate**, **1,176 invalid**, **1,200 conflicting** (600 pairs). These are expected acceptance targets, not observed results. See [data-manifest.md](data-manifest.md).

## 3. MVP scope

**In scope:** deterministic synthetic branch/product/sales data; CSV ingestion; schema and business-rule validation; normalization; duplicate/conflict handling; rejected-record report; idempotent PostgreSQL load; branch-level revenue, unique sales count, average ticket; run metadata, logs, automated tests, GitHub Actions workflow, sanitized downloadable artifacts.

**Out of scope:** real customer data, external source APIs, persistent databases, public REST API, cloud services outside GitHub, self-hosted runners, Airflow, Spark, Kafka, production SLAs, returns, taxes, discounts, and stock management.

## 4. Stakeholders and user stories

- **Data engineer:** As a data engineer, I want to process a batch repeatedly without creating duplicates, so that failures and reruns do not corrupt results.
- **Data quality analyst:** As an analyst, I want every rejected record to have a reason and source reference, so that errors can be investigated.
- **Retail manager:** As a manager, I want consistent revenue and ticket metrics per branch, so that I can compare performance.
- **Reviewer:** As a GitHub visitor, I want automated test evidence and reports, so that I can assess the solution without external infrastructure.

## 5. Functional requirements

| ID | Requirement |
| --- | --- |
| RF-001 | Read synthetic CSV inputs for branches, products, and sales. |
| RF-002 | Validate required columns, types, and mandatory values. |
| RF-003 | Normalize supported dates, identifiers, and currency values. |
| RF-004 | Detect exact duplicates and same-key conflicting sales. |
| RF-005 | Separate accepted and rejected records with reason codes. |
| RF-006 | Load accepted data into temporary PostgreSQL with referential integrity. |
| RF-007 | Produce per-branch revenue, unique sales count, and average ticket. |
| RF-008 | Record execution ID, status, input/accepted/rejected/duplicate/conflict counts, and sanitized diagnostics. |
| RF-009 | Support reprocessing of an identical batch without changing analytical results. |
| RF-010 | Export analytical reports, quality metrics, and test evidence as GitHub Actions artifacts. |

## 6. Business rules

- **RN-001:** A sale is identified by the composite key (branch_id, sale_id).
- **RN-002:** A sale is accepted only if its branch and product exist in valid reference data.
- **RN-003:** Monetary values use BRL with exactly two decimal places after normalization. Negative and zero-value sales are invalid. Exact accepted input formats are to be defined in the technical plan.
- **RN-004:** Supported date formats must be explicit and unambiguous; valid dates normalize to ISO 8601, impossible or unsupported dates are rejected.
- **RN-005:** Identical records with the same sale key are counted as duplicates and loaded once. Different records sharing a sale key are conflicts and must not enter the analytical dataset until resolved. Conflicts take precedence over choosing an arbitrary winner.
- **RN-006:** Invalid records are excluded from analytics and included in a rejection report with source identification and reason code.
- **RN-007:** Repeating an unchanged batch in the same temporary database does not change sale counts or revenue.
- **RN-008:** Each sales row represents one product transaction. Revenue equals its normalized transaction amount; average ticket equals total revenue divided by unique accepted sales for a branch. For zero accepted sales, average ticket is reported as null (not divided by zero).
- **RN-009:** All business data is fictional and deterministic; no real personally identifiable data is allowed.

## 7. Acceptance criteria

**CA-001 — Valid batch:** Given 100 unique valid sales and valid reference data, when the pipeline runs, then exactly 100 sales are loaded and included in analytics.

**CA-002 — Exact duplicates:** Given 100 structurally valid sales rows with 10 exact repeat rows and no conflicting keys, when processed, then exactly 90 unique sales are loaded and 10 duplicate rows are reported.

**CA-003 — Invalid records:** Given 100 sales rows with 5 invalid rows and 95 valid unique rows, when processed, then 95 are accepted and 5 are rejected with reasons.

**CA-004 — Idempotency:** Given a successfully loaded batch, when the same batch is loaded again into the same database, then sale counts and revenue remain unchanged.

**CA-005 — Interrupted load:** Given a simulated failure during loading, when the load is retried, then there are no inconsistent partial results or duplicate sales.

**CA-006 — Evidence:** Given a completed workflow, when its GitHub Actions run is inspected, then test results, run summary, quality metrics, and analytical report are available as sanitized artifacts.

**CA-007 — Conflicting key:** Given two different sales rows with the same composite business key, when validated, then neither conflicting version is silently selected and the conflict is reported.

**CA-008 — Referential integrity:** Given a sale referencing an unknown branch or product, when validated, then the sale is rejected and excluded from metrics.

**CA-009 — Revenue reconciliation:** Given a batch with known accepted transaction amounts, when analytics are generated, then the sum of per-branch revenue equals the sum of accepted unique sales amounts.

**CA-010 — Security:** Given the repository and a workflow run, when reviewed, then no actual secrets or credentials are exposed in versioned files or logs.

## 8. Non-functional constraints

- GitHub-hosted Actions only; ephemeral PostgreSQL service container.
- Runtime configuration via environment variables; GitHub Secrets for real secrets if needed.
- No external hosted business-data sources or infrastructure.
- Deterministic inputs and reproducible execution.
- Least-privilege workflow permissions, explicit artifact retention, and no secrets in reports.
- Automated tests linked to requirements and acceptance criteria.

## 9. Success conditions

All mandatory acceptance criteria pass; no duplicate accepted sale keys; every rejected row has a reason; analytical totals reconcile; no committed credentials; the workflow produces reviewable evidence.

## 10. Open questions (not approved assumptions)

1. **Resolved:** 100,000 sales input rows, with the approved category counts in the data manifest.
2. Which source date formats and BRL amount formats will be accepted?
3. What exact CSV schemas, null rules, and rejection reason codes will be used?
4. What are the workflow artifact retention and package dependency pinning policies?
5. How will partial failure be injected and demonstrated reproducibly?

The technical plan proposes answers to questions 2–5. Verify outstanding security and dependency decisions before implementation.
