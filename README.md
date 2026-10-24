# DataFlow Engineering

> Spec-Driven Data Engineering | NexaRetail (fictional retail company)

A portfolio project to design and validate a reproducible retail data pipeline using **Spec-Driven Development (SDD)**. The project models data from five fictional retail branches, validates and transforms sales records, and produces trustworthy analytical reports.

> **Status: specification phase.** The pipeline, automated tests, and workflows are planned, not yet implemented. No performance or reliability claims are made at this stage.

## Business problem

NexaRetail receives sales and reference data from multiple branches with inconsistent formats, duplicated transactions, invalid product references, and incomplete records. The goal is to consolidate these sources into reliable sales metrics, while keeping rejected records and processing decisions auditable.

## Planned MVP

- Deterministic, synthetic datasets for branches, products, and sales
- CSV ingestion and schema validation
- Date, identifier, and monetary-value normalization
- Duplicate detection, conflict handling, and rejection reports
- Idempotent loads into an ephemeral PostgreSQL instance
- Per-branch revenue, transaction counts, and average ticket
- Automated tests, quality metrics, and sanitized execution logs
- GitHub Actions orchestration and downloadable workflow artifacts

## Planned architecture

```text
Synthetic CSV datasets
        |
        v
Ingestion -> Validation -> Normalization -> Quality checks
                                            |
                               +------------+------------+
                               |                         |
                          Valid records            Rejected records
                               |                         |
                               v                         v
                    Ephemeral PostgreSQL         Quality report
                               |
                               v
                     Analytical aggregation
                               |
                               v
                    GitHub Actions artifacts
```

All processing will run on **GitHub-hosted Actions runners**. PostgreSQL will be a temporary service container, not a persistent external database. Reports and sanitized logs will be stored as workflow artifacts subject to GitHub retention limits.

## Security and infrastructure constraints

- No hardcoded credentials or committed secrets
- Runtime configuration through environment variables; GitHub Actions secrets for actual sensitive values
- A tracked `.env.example` may document variable names, but a populated `.env` must never be committed
- No third-party cloud services, self-hosted runners, or personally operated infrastructure
- No external data APIs at runtime: the business data is entirely synthetic
- Least-privilege GitHub Actions permissions and no sensitive values in logs
- No assumption of persistent state across independent workflow runs

## SDD workflow

We will document requirements and acceptance criteria before implementation, then trace each task and test back to the approved specification.

| Phase | Deliverable | Status |
| --- | --- | --- |
| Business requirements | Initial project scope | Draft |
| Constitution | Architecture and engineering principles | Planned |
| Specification | Versioned requirements and acceptance criteria | Planned |
| Technical plan | Data contracts, design, and trade-offs | Planned |
| Tasks | Testable implementation tasks | Planned |
| Implementation | Pipeline, tests, and GitHub Actions | Not started |

## Technology choices (planned)

Python, PostgreSQL, SQL, pytest, and GitHub Actions. Additional dependencies will be selected and justified in the technical plan; they are not requirements yet.

## Repository

This repository is intended as an educational and professional data engineering portfolio case study. **NexaRetail is fictional; no real customer, employee, or financial data is used.**

## Current next step

Approve the SDD constitution and the first versioned specification before writing implementation code.
