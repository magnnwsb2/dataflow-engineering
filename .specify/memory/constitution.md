# DataFlow Engineering Constitution

**Version:** 1.0.0  
**Status:** Approved baseline for planning; changes require a documented revision  
**Project:** DataFlow Engineering — NexaRetail (fictional)

## Purpose

Build a reproducible, auditable retail data engineering portfolio project using Spec-Driven Development (SDD). These principles govern requirements, design, tasks, implementation, tests, and GitHub workflows.

## Non-negotiable principles

### P-001 — GitHub-only execution and collaboration
Source code, documentation, issues, reviews, CI/CD, execution, and deliverables MUST live within the GitHub ecosystem. Execution MUST use GitHub-hosted Actions runners; no self-hosted runners, privately operated machines, external cloud infrastructure, or third-party hosted data services. GitHub-hosted compute is ephemeral infrastructure provided by GitHub, not an always-on server. Workflow dependency installation may use package registries as needed; this is not authorization to send business data to external APIs.

### P-002 — Secrets and configuration
Application and workflow configuration MUST come from environment variables. Actual secrets, when needed, MUST use GitHub Actions secrets and least-privilege permissions. Credentials, access tokens, populated .env files, and sensitive data MUST NOT be committed or printed. Only documented placeholders in .env.example are allowed. The temporary database MUST use an isolated test credential supplied at runtime; never reuse production credentials.

### P-003 — Ephemeral, reproducible storage
PostgreSQL MUST run as a temporary service container in a GitHub Actions job and be discarded afterward. Each independent run MUST recreate its schema and load synthetic inputs without depending on prior database state. Idempotency MUST be verified by repeating loads within one run. GitHub artifacts MUST contain sanitized reports and test evidence only, with retention configured and documented.

### P-004 — Specification-first changes
Before implementing behavior, the corresponding requirement, business rule, acceptance scenario, and traceable task MUST be documented. Technical decisions MUST be recorded in the plan or an ADR. Changes to expected behavior MUST update the specification and tests in the same change set. No implementation code before the initial specification and technical plan are reviewed.

### P-005 — Data correctness and integrity
The pipeline MUST separate raw input, validated records, rejected records, and analytical outputs. Every rejection MUST have a stable reason code and traceable source identifier. Exact duplicate business keys with identical content MUST be loaded only once; conflicting records MUST be rejected deterministically. Monetary arithmetic MUST be decimal-safe, not binary floating-point.

### P-006 — Testability and reliability
Every mandatory acceptance criterion MUST have an automated test or verifiable workflow check. Tests MUST cover valid data, malformed data, referential integrity, duplicates, conflicts, idempotency, and a simulated interrupted load. Loads MUST avoid partial inconsistent states, using transactional boundaries as specified in the technical plan. A successful workflow MUST not hide failed tests or quality checks.

### P-007 — Observability and privacy
Every execution MUST have a run identifier, timestamps, status, record counts, rejection counts, and sanitized error diagnostics. Only synthetic business data may be used. Logs and artifacts MUST not expose credentials, tokens, or personally identifiable real-world data. Metrics and reports MUST reconcile to the source inputs.

### P-008 — Simplicity and scope control
The MVP MUST use Python, SQL, PostgreSQL, pytest, and GitHub Actions. Additional dependencies require a documented need. Airflow, Kafka, Spark, externally hosted databases, and publicly deployed APIs are out of scope. Do not claim scale, performance, or production readiness without evidence.

### P-009 — Reviewable, reproducible delivery
Use readable names, documented data contracts, small cohesive modules, deterministic synthetic fixtures, and meaningful commits. All project artifacts needed to understand or reproduce the pipeline MUST be versioned in GitHub or produced by a documented GitHub Actions workflow. GitHub Actions artifacts are temporary and are not a substitute for versioned specifications.

## Quality gates

A change is ready only when: (1) its requirement and acceptance test are traceable; (2) all relevant tests pass; (3) no secrets are committed; (4) workflow permissions are minimal; (5) output counts and analytical totals reconcile; and (6) documentation reflects the current implementation.

## Governance

This constitution takes precedence over lower-level plans and tasks. Changes require a version bump, rationale, impact assessment, and a GitHub commit or pull request. MAJOR: incompatible principle change; MINOR: new principle or substantial expansion; PATCH: clarification. Any exception MUST be explicitly documented and approved before implementation.

## Open decisions

- Synthetic dataset volume: **100,000 input sales rows approved**, distributed as 94,618 accepted unique, 3,006 exact duplicate, 1,176 invalid, and 1,200 conflicting rows; see [data manifest](../../specs/001-retail-sales-pipeline/data-manifest.md).
- Exact CSV field contracts, supported date formats, monetary precision, and analytical schema: technical planning.
- GitHub Actions artifact retention period and dependency pinning: technical planning.
