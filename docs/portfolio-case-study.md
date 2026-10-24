# Case Study | NexaRetail Data Engineering Pipeline

> **Portfolio project** · Python 3.12 · PostgreSQL 16 · SQL · pytest · GitHub Actions

## Executive summary

Built a reproducible end-to-end data pipeline for **NexaRetail**, a fictional five-branch retailer. The pipeline generates synthetic sales, validates business rules, audits every input row, loads accepted sales into PostgreSQL, checks replay idempotency and exports branch-level analytics.

**Verified acceptance run:** 100,000 source sales rows; 94,618 accepted unique sales; 0 additional inserts on replay; five branch reports. All monetary results are **synthetic**, not real business revenue.

## The problem

Sales from multiple branches can arrive with invalid dates or amounts, unknown reference IDs, exact duplicates and conflicting records that share the same business key. A naive load could double-count revenue or silently overwrite inconsistent transactions.

**Engineering goal:** produce reliable, traceable metrics while rejecting bad input and ensuring repeatable loads.

## Architecture

```text
Synthetic CSV generator (seed: 20271024)
                 |
                 v
        Bronze / raw CSV
                 |
                 v
       Validation + normalization
          /              \
         v                v
 Accepted unique     Audit dispositions
         |            (accepted / duplicate /
         |             invalid / conflict)
         v                |
 PostgreSQL 16            v
 dim_branch           Sanitized audit CSV
 dim_product
 fact_sale
         |
         v
 Gold SQL aggregation
         |
         v
 sales_by_branch.csv + JSON summaries
         |
         v
 GitHub Actions downloadable artifacts
```

All database execution is performed against an **ephemeral PostgreSQL service container**. No persistent production database, cloud data warehouse or real customer data is used.

## Key engineering decisions

| Decision | Rationale |
| --- | --- |
| Deterministic generator and SHA-256 manifest | Reproduce the same input and check file identity |
| Business key `(branch_id, sale_id)` | Prevent duplicate sale identity |
| Reject all variants of conflicting keys | Avoid arbitrarily choosing contradictory payloads |
| `Decimal` / PostgreSQL `NUMERIC` | Avoid binary floating-point errors in currency |
| Transactional PostgreSQL load | Roll back writes if a conflicting existing record is detected |
| Same-run replay | Demonstrate idempotency for an identical batch |
| Sanitized row audit | Trace input classification without exposing raw payload |
| GitHub Actions PostgreSQL service | Reproducible tests without maintaining external infrastructure |

## Verified data quality

| Disposition | Rows | Share |
| --- | ---: | ---: |
| Accepted unique | 94,618 | 94.618% |
| Exact duplicates | 3,006 | 3.006% |
| Invalid | 1,176 | 1.176% |
| Conflicts | 1,200 | 1.200% |
| **Input total** | **100,000** | **100%** |

Invalid records include missing required fields, invalid dates and amounts, nonpositive quantities, mismatched totals and unknown branches/products.

## Verified Gold output

| Branch | Unique sales | Synthetic revenue (BRL) |
| --- | ---: | ---: |
| F001 | 18,924 | 106,625,921.68 |
| F002 | 18,924 | 106,569,716.22 |
| F003 | 18,924 | 105,717,955.14 |
| F004 | 18,923 | 106,725,190.29 |
| F005 | 18,923 | 106,435,309.87 |
| **Total** | **94,618** | **532,074,093.20** |

Weighted consolidated average ticket: **BRL 5,623.39**.

## Execution evidence

**NexaRetail end-to-end #2**

- GitHub Actions conclusion: **Success**
- Branch / commit: `main` / `e7f7931`
- Overall workflow duration: **2m 07s**
- First PostgreSQL load: **94,618 inserted**
- Identical-batch replay: **0 inserted**
- Persisted fact rows: **94,618**
- Unit tests from JUnit XML: **11 passed, 0 failures, 0 errors**
- Downloadable report artifact: `nexaretail-reports`

**PostgreSQL integration #1**

- GitHub Actions conclusion: **Success**
- Branch / commit: `main` / `3e7e961`
- Overall workflow duration: **3m 40s**
- JUnit test count not independently reconciled from its artifact.

[End-to-end workflow](https://github.com/magnnwsb2/dataflow-engineering/actions/workflows/pipeline.yml) · [PostgreSQL integration workflow](https://github.com/magnnwsb2/dataflow-engineering/actions/workflows/postgres-integration.yml) · [Detailed validation results](validation-results.md)

## What this project demonstrates

- Python-based ingestion and data normalization
- Explicit data quality and exception-handling policies
- SQL modeling and PostgreSQL referential integrity
- Transactional writes and duplicate protection
- Data reconciliation and audit trails
- Automated testing and CI orchestration
- Business-facing reporting with verifiable source metrics

## Limitations and next improvements

This is an educational, synthetic-data case study. Successful test runs do **not** demonstrate production-scale throughput, multi-run persistence, disaster recovery or a security certification. The 2m 07s duration is the overall CI job time, not a measured ingestion benchmark.

Possible extensions: configurable incremental batches, optimized bulk loading, additional observability, partitioned processing and performance measurements under controlled conditions.

## Interview-ready explanation

> I built a reproducible retail data pipeline in Python and PostgreSQL that processes 100,000 synthetic sales records. It validates data quality, rejects conflicting business keys, records an audit trail and generates branch-level revenue reports. In a verified GitHub Actions run, 94,618 unique sales were inserted, and replaying the same batch inserted zero additional records. I also automated unit and PostgreSQL integration workflows to validate the pipeline without a persistent database.

NexaRetail, its branches, transactions and revenue are fictional.
