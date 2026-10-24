# ADR-001 — Secure PostgreSQL and GitHub Actions Execution

**Status:** Proposed — requires verification during T003  
**Scope:** 001-retail-sales-pipeline  
**Date:** 2026-10-24

## Context

The constitution requires GitHub-hosted runners, an ephemeral PostgreSQL service container, no hardcoded credentials, and sanitized artifacts. GitHub Actions must run integration tests and the 100,000-row pipeline without external infrastructure.

## Decision

1. Use a GitHub-hosted Ubuntu runner with a PostgreSQL service container in the same job.
2. Set a dedicated **repository Actions secret** named `CI_POSTGRES_PASSWORD` through GitHub repository Settings > Secrets and variables > Actions. The actual value must be generated securely by the repository owner and never committed or pasted into chat.
3. Inject that secret into the PostgreSQL container's `POSTGRES_PASSWORD` environment and the application process's `DB_PASSWORD` environment. Set `POSTGRES_USER` and `POSTGRES_DB` to clearly nonproduction identifiers. Avoid printing any connection string.
4. Use the runner's localhost mapped PostgreSQL port, a readiness/health check, and parameterized SQL. Never use `trust` authentication as a workaround.
5. Declare minimal job permissions (`contents: read`), pin Actions to reviewed immutable commit SHAs, pin Python dependencies, set a job timeout, and use a controlled artifact retention period of 14 days subject to repository policy.
6. Trigger CI on pull requests and pushes to main. Keep the full pipeline manual (`workflow_dispatch`) until a schedule is explicitly approved.
7. On failure, publish sanitized diagnostics with `if: always()`, but do not suppress nonzero test/pipeline exit status.
8. Validate whether secret expressions are accepted in the chosen `services.<name>.env` syntax when authoring YAML. If GitHub restrictions prevent this exact mechanism, document a constitution-compliant alternative and revise this ADR **before implementing the workflow**.

## Consequences

- The repo owner must configure the Actions secret; the workflow cannot succeed without it.
- Every run starts with an empty database; idempotency must be demonstrated by replaying within the same job.
- No persistence across runs is claimed.
- GitHub Actions artifacts expire and are not a permanent data store.
- This ADR documents a design; it is not evidence that credentials, workflows, or runners have already been configured or tested.

## Rejected alternatives

- Hardcoded password in YAML or source: violates P-002.
- PostgreSQL `trust` authentication: weakens authentication.
- Persistent managed PostgreSQL outside GitHub: violates P-001/P-003.
- Self-hosted runner: violates P-001.
