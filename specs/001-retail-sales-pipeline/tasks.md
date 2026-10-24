# Implementation Tasks — NexaRetail Retail Sales Pipeline

**Feature:** 001-retail-sales-pipeline  
**Version:** 0.1.0  
**Status:** Planned — business distribution approved; technical readiness checks remain  
**Dataset:** 100,000 synthetic sales input rows  
**Sources:** [spec.md](spec.md), [plan.md](plan.md), [constitution](../../.specify/memory/constitution.md)

## Execution rules

- Tasks are ordered by dependencies. A task is complete only after its acceptance checks and documentation are committed.
- Do not start implementation until remaining technical readiness and security decisions are verified; the business scope and dataset category counts are approved.
- Follow test-first where practical; tests must link to RF/RN/CA identifiers.
- Use GitHub-hosted runners and ephemeral PostgreSQL only. Do not use external business data, cloud infrastructure, or self-hosted runners.
- `[ ]` means pending; check a task only when its deliverable and evidence exist. This file is a plan, not a claim that code or workflows already exist.
- A single task may span multiple small commits or pull requests. Keep the `main` branch passing after CI is introduced.

## Phase 0 — Specification gate (blocking)

- [ ] **T001** Record approval of `spec.md` and `plan.md` business scope and dataset counts; review remaining technical assumptions, money/date formats, conflict policy, PostgreSQL design, and GitHub Actions security. **Evidence:** documented approval/decision log. **Links:** P-004, RF-001–010.
- [ ] **T002** Validate the approved synthetic anomaly manifest for exactly 100,000 sales input rows: 94,618 accepted unique, 3,006 exact duplicates, 1,176 invalid, and 1,200 conflicting rows (600 pairs). Include fixed seed, generator version, row fingerprints, and expected reconciliation totals. **Evidence:** documented invariant `input = accepted + duplicate + invalid + conflict`. **Links:** RF-004/005/008, CA-002/003/007/009.
- [ ] **T003** Verify how to securely supply ephemeral PostgreSQL credentials to GitHub Actions service containers without hardcoded secrets; decide whether a GitHub Actions secret is needed and document setup. Confirm supported versions, action SHA pinning, dependency lock/pinning, and artifact retention. **Evidence:** ADR or plan update. **Links:** P-001/002/003, CA-010.

**Gate:** No coding before T001–T003.

## Phase 1 — Repository and project setup

- [ ] **T004** Establish Python package layout under `src/dataflow/`, test directories, and minimal command entry points. **Evidence:** import smoke test. **Links:** P-008/009.
- [ ] **T005** Add pinned dependency declarations and a documented `.env.example` with variable names only; verify `.gitignore` does not exclude source/specs/tests. **Evidence:** clean checkout installs without local secrets. **Links:** P-002/009, CA-010.
- [ ] **T006** Add developer documentation for GitHub-only execution, configuration, reproducibility, and artifact lifecycle. **Evidence:** README/docs updated. **Links:** P-001/003/009.

**Gate:** Project skeleton and dependency installation are reproducible.

## Phase 2 — Deterministic synthetic data

- [ ] **T007** Implement generator for exactly 5 branch records and 200 product records satisfying contracts. **Evidence:** deterministic fixture tests. **Links:** RF-001, RN-002.
- [ ] **T008** Implement 100,000-row sales generator with fixed seed and versioned anomaly manifest; avoid committing full generated data. **Evidence:** byte-for-byte or canonical-hash reproducibility tests and exact row-count checks. **Links:** RF-001/004, RN-009.
- [ ] **T009** Add small checked-in synthetic sample fixtures for focused tests, including valid rows and every anomaly type. **Evidence:** fixtures mapped to test cases. **Links:** CA-001/002/003/007/008.

**Gate:** Same seed and generator version yield identical inputs and expected manifest counts.

## Phase 3 — Bronze ingestion and contract validation

- [ ] **T010** Implement streaming CSV ingestion with UTF-8/header validation, source filename, physical/logical record number, and deterministic input fingerprint. **Evidence:** CSV edge-case tests. **Links:** RF-001/002.
- [ ] **T011** Validate reference CSVs (required columns, ID format, uniqueness, mandatory fields); fail the batch on invalid reference schema or records. **Evidence:** reference validation tests. **Links:** RF-002, RN-002.
- [ ] **T012** Parse and normalize dates, IDs, quantity, and decimal money strictly per `plan.md`; enforce `total_amount = quantity × unit_price`. **Evidence:** valid/invalid locale and boundary tests. **Links:** RF-002/003, RN-003/004, CA-003.
- [ ] **T013** Validate sale references against known branches/products and emit stable rejection codes. **Evidence:** missing reference tests. **Links:** RF-005, RN-002/006, CA-008.

**Gate:** No malformed or unsupported sales row silently reaches the load stage.

## Phase 4 — Silver quality and deduplication

- [ ] **T014** Define canonical normalized payload/fingerprint and business key `(branch_id, sale_id)`. **Evidence:** stable equality tests. **Links:** RF-004, RN-001/005.
- [ ] **T015** Classify exact duplicate rows, keeping one canonical occurrence and counting extras separately. **Evidence:** 100-row/10-duplicate acceptance fixture yields 90 unique sales. **Links:** RF-004/005, CA-002.
- [ ] **T016** Reject every row in a same-key conflicting group deterministically; do not select a winner based on file order. **Evidence:** permutation/order-independence tests. **Links:** RF-004/005, CA-007.
- [ ] **T017** Export sanitized rejected-row references, disposition/reason codes, and reconcile `input = accepted + invalid + duplicate + conflict`. **Evidence:** invalid-row and accounting tests. **Links:** RF-005/008, RN-006, CA-003.

**Gate:** Every input sales row has exactly one disposition; conflict handling is deterministic.

## Phase 5 — PostgreSQL storage and reliable loading

- [ ] **T018** Create versioned SQL schema for `dim_branch`, `dim_product`, `fact_sale`, `pipeline_run`, `rejected_row` with primary/foreign keys, CHECK constraints, and appropriate numeric precision. **Evidence:** schema constraint tests. **Links:** RF-006/008, RN-001/002/003.
- [ ] **T019** Implement PostgreSQL connection using environment variables and parameterized SQL, with sanitized connection errors. **Evidence:** service-container integration test; no secret output. **Links:** P-002, CA-010.
- [ ] **T020** Load dimensions and accepted sales transactionally, with run metadata and rejection references; prevent inconsistent partial states. **Evidence:** integration test for 100 valid sales. **Links:** RF-006/008, CA-001.
- [ ] **T021** Implement idempotent replay within the same database, distinguish inserted from already-present records, and explicitly reject divergent existing-key payloads. **Evidence:** repeated-batch test with unchanged counts/revenue. **Links:** RF-009, RN-007, CA-004.
- [ ] **T022** Inject failure after partial insert but before commit; assert rollback and successful retry. **Evidence:** deterministic interruption/recovery integration test. **Links:** P-006, CA-005.

**Gate:** Transaction boundaries, foreign keys, and replay behavior are demonstrated with PostgreSQL, not mocks alone.

## Phase 6 — Gold reporting and observability

- [ ] **T023** Implement SQL analytics for all five branches, including zero-sale branches: revenue, unique sale count, average ticket (null if no sales). **Evidence:** known-answer fixtures. **Links:** RF-007, RN-008.
- [ ] **T024** Add reconciliation checks: source disposition totals, fact row counts, sum of branch counts, and total revenue equality. **Evidence:** failing test on deliberately corrupted expectations. **Links:** RF-007/008, CA-009.
- [ ] **T025** Export `sales_by_branch.csv`, `quality_summary.json`, `rejections.csv`, `run_summary.json` with execution ID, timestamps, status, counts, and no secrets. **Evidence:** schema/content tests for each report. **Links:** RF-008/010, CA-006/010.

**Gate:** Every accepted sale is reflected exactly once in analytics, and every nonaccepted row is accounted for.

## Phase 7 — Acceptance testing and reliability

- [ ] **T026** Build unit suite for parsing, normalization, duplicate/conflict classification, rejection codes, and data generation. **Evidence:** pytest passing, requirement IDs documented. **Links:** RF-001–005, CA-002/003/007.
- [ ] **T027** Build PostgreSQL integration suite for referential integrity, transactional load, idempotency, and rollback/retry. **Evidence:** pytest integration passing on Actions service container. **Links:** RF-006/009, CA-001/004/005/008.
- [ ] **T028** Build full 100,000-row end-to-end acceptance test and reconcile actual outputs with the approved anomaly manifest. **Evidence:** run summary and test result artifact. **Links:** RF-001–010, CA-009.
- [ ] **T029** Add security and workflow-output checks: no real secrets in tracked files/logs/artifacts, read-only permissions, and predictable failure statuses. **Evidence:** review checklist and CI checks. **Links:** P-002/007, CA-010.

**Gate:** All CA-001 through CA-010 have passing evidence, not only manually observed results.

## Phase 8 — GitHub Actions and portfolio delivery

- [ ] **T030** Create `.github/workflows/ci.yml` for pull requests and main pushes, with unit/integration tests, ephemeral PostgreSQL, minimal permissions, pinned actions, timeouts, and JUnit artifacts. **Evidence:** successful Actions CI run. **Links:** RF-010, CA-006.
- [ ] **T031** Create manually triggered `.github/workflows/pipeline.yml` for deterministic 100,000-row generation, ETL, reconciliation, replay validation, and sanitized artifact uploads; do not add a schedule without approval. **Evidence:** completed workflow run and downloadable reports. **Links:** RF-001–010, CA-006/009.
- [ ] **T032** Ensure failure-path diagnostics are uploaded even if tests or ETL fail, without marking a failed run successful. **Evidence:** intentionally failing workflow test. **Links:** P-006/007, CA-006.
- [ ] **T033** Update README with verified architecture, reproduction instructions, test results, metrics, screenshots or links to actual Actions evidence, and honest limitations (ephemeral DB, no production claims). **Evidence:** reviewer can inspect all artifacts from GitHub. **Links:** P-009, CA-006.
- [ ] **T034** Final SDD review: verify constitution compliance, traceability matrix, 100,000-row manifest reconciliation, clean secrets review, and all acceptance gates. **Evidence:** documented release checklist. **Links:** P-001–009, RF-001–010, CA-001–010.

**Gate:** The GitHub repository is a reproducible, reviewable portfolio case study.

## Dependency order

```text
T001–T003 (approval)
       |
T004–T006 (setup)
       |
T007–T009 (fixtures)
       |
T010–T013 (ingestion)
       |
T014–T017 (quality)
       |
T018–T022 (storage/recovery)
       |
T023–T025 (analytics)
       |
T026–T029 (acceptance)
       |
T030–T034 (Actions/evidence)
```

Tests should be developed alongside the relevant features, even though the final suite is consolidated in Phase 7. `ci.yml` may be introduced early once its minimum prerequisites exist; the diagram is a release dependency sequence, not a prohibition on earlier CI.

## Acceptance criteria traceability

| Acceptance criterion | Primary tasks |
| --- | --- |
| CA-001: valid batch | T009, T020, T027 |
| CA-002: duplicates | T008, T015, T026 |
| CA-003: invalid rows | T012, T017, T026 |
| CA-004: idempotency | T021, T027 |
| CA-005: interrupted load | T022, T027 |
| CA-006: artifacts | T025, T030–T033 |
| CA-007: conflicts | T016, T026 |
| CA-008: referential integrity | T011, T013, T027 |
| CA-009: revenue reconciliation | T023, T024, T028 |
| CA-010: security | T005, T019, T029, T034 |

## Definition of done

A task is complete when: its implementation or document is committed; linked tests/checks pass; no secrets are exposed; the documented behavior matches the specification; any design changes are reflected in `plan.md` and `spec.md`; and evidence can be inspected in GitHub.

## Immediate next action

The business scope and anomaly category counts are approved and documented. Complete technical/security review (T001/T003) and verify the manifest through automated generation tests (T002). Only then begin T004. **No pipeline implementation has started.**
