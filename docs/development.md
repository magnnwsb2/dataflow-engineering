# Development and execution guide

**Status:** Initial Python package skeleton only. The pipeline, database integration, and GitHub Actions workflows do not yet exist.

## Requirements

- Python 3.12 or 3.13 (proposed; not yet validated on GitHub runners).
- Git and access to this GitHub repository.

## Local optional smoke test

This is an optional developer convenience, **not** a deployment/runtime architecture. All project acceptance runs will be hosted on GitHub Actions.

```bash
python -m pip install -e '.[test]'
python -m pytest
python -m dataflow
```

The package command prints that the pipeline is not yet implemented. A passing smoke test does not validate the data pipeline.

## Configuration

See [../.env.example](../.env.example) for variable names. Do not commit `.env` or secrets. Configure `CI_POSTGRES_PASSWORD` in GitHub Actions repository secrets before integration workflows are introduced. Use separate, non-production test credentials.

## GitHub-only target execution

Planned workflows will run on GitHub-hosted Ubuntu runners. PostgreSQL will be a temporary service container within each job. Source CSVs will be generated deterministically at runtime; reports and sanitized test evidence will be uploaded as Actions artifacts with finite retention.

No real customer data, external runtime APIs, persistent hosted database, or self-hosted runners.

## Reproducibility and evidence

The approved synthetic distribution is 100,000 input rows: 94,618 valid unique, 3,006 duplicates, 1,176 invalid, 1,200 conflicting. These counts are **specification targets**, not achieved results. See [../specs/001-retail-sales-pipeline/data-manifest.md](../specs/001-retail-sales-pipeline/data-manifest.md).

Before CI implementation, pin exact package versions, GitHub Action SHAs, and the PostgreSQL image digest; record actual test runs and outcomes only after execution.
