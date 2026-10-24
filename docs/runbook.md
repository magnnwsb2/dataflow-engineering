# NexaRetail — execution and verification runbook

## Preconditions

- Python 3.12 and PostgreSQL 16 in the ephemeral GitHub Actions runner.
- The repository Actions secret `CI_POSTGRES_PASSWORD` must be configured by the owner.
- Never commit credentials, raw customer data or generated input CSVs.

## Unit checks

The **Python CI** workflow runs on pushes and pull requests. A green result
confirms unit tests only; it is not proof of database integration.

## Database integration

Run **PostgreSQL integration** from the repository Actions tab. This creates
an ephemeral PostgreSQL service and executes the integration tests. Review the
test report artifact and confirm a green conclusion.

## End-to-end acceptance

Run **NexaRetail end-to-end** from Actions > workflow_dispatch. A passing run
must demonstrate:

| Check | Required value |
| --- | ---: |
| Sales input rows | 100,000 |
| Accepted unique | 94,618 |
| Exact duplicate rows | 3,006 |
| Invalid rows | 1,176 |
| Conflicting rows | 1,200 |
| First-run fact inserts | 94,618 |
| Replay inserts | 0 |
| Final fact count | 94,618 |
| Branch rows in Gold | 5 |

The workflow publishes `nexaretail-reports` with `row_audit.csv`,
`quality_summary.json`, `run_summary.json` and `sales_by_branch.csv`.
Artifacts expire after 14 days.

If the service fails to start, verify that the Actions secret exists.
Do not put the secret in an issue, chat message, workflow file, or log.

If a test fails, preserve the failing run URL, inspect its job log and JUnit
report, and fix the cause before claiming completion.

**Status:** this runbook is an acceptance procedure, not evidence of a
successful run. The database is discarded when the job finishes.
