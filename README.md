# fan-unification-platform

A fan identity-resolution and data-warehouse platform for a fictional national soccer
federation: four messy source systems (a Salesforce-style CRM, ticketing, merch, and email
marketing) are ingested through Prefect-orchestrated pipelines into an S3-style lake and a
Postgres star-schema warehouse, unified into golden fan records with **measured** matching
accuracy, and published as BI marts and dashboards.

> **All data in this repository is synthetic.** It is produced by a seeded generator that
> also emits ground truth, which is what makes the unification accuracy measurable. No real
> member, fan, or customer data appears anywhere, and no LLM is used anywhere in the runtime
> path.

**Status: M0 (scaffold).** Sections below are labeled `planned` until their milestone lands.

## Architecture

```
 synthetic source systems              lake (MinIO/S3 API)         warehouse (Postgres 16)
┌──────────────────────────┐          ┌──────────────────┐        ┌─────────────────────────────┐
│ mock Salesforce REST API │─extract─▶│ raw/<source>/    │─COPY──▶│ raw → staging → identity →  │
│ ticketing JSONL drops    │ (Prefect │   dt=.../batch.* │        │ core (star) → marts         │
│ merch CSV exports        │  flows)  └──────────────────┘        │ + ops (audit/dq)            │
│ email-marketing events   │                                      └──────────────┬──────────────┘
└──────────────────────────┘   Splink unification (DuckDB engine) ◀── parquet ────┤
                               xref + golden dim_fan written back ────────────────┤
                                                                                  ▼
                                                    Evidence.dev site → GitHub Pages
```

Postgres stands in for AWS Redshift (which it derives from) so the project costs $0 to run;
`warehouse/redshift/` and `infra/terraform/` carry the real-Redshift variants — see
`docs/redshift-migration.md` (`planned`).

## Quickstart

```sh
docker compose up -d --build   # postgres + minio + prefect server + mock salesforce
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e .[dev]
fanuni info                    # verify config resolution
```

End-to-end demo (`planned`, M6): `fanuni demo` — generate → ingest → transform → unify →
quality gates → dashboards.

## Milestones

| Milestone | Delivers | Status |
| --- | --- | --- |
| M0 | Scaffold, compose stack, CI green from commit one | **done** |
| M1 | Seeded synthetic sources + ground-truth entity map, mock Salesforce API | planned |
| M2 | Prefect extract/load: lake raw zone, COPY loads, watermarks, quarantine, backfills | planned |
| M3 | SQL runner, staging, star schema, data-quality assertion framework | planned |
| M4 | Identity resolution: deterministic + Splink, golden `dim_fan`, measured precision/recall | planned |
| M5 | Production ops: nightly scheduled run, retries/alerting, failure drills, performance pass | planned |
| M6 | Evidence.dev dashboards on GitHub Pages, docs, cold-clone verification | planned |

## CI

| Job | Proves |
| --- | --- |
| `lint` | ruff check + format |
| `typecheck` | mypy over `src` and `tests` |
| `test` | unit tests |
| `docker` | the mock-Salesforce image builds |
| `gitleaks` | no secrets in history |
| `integration` (`planned`, M2) | the whole pipeline runs end-to-end against real services |
| `terraform` (`planned`, M5) | the Redshift/S3 IaC validates |
| `site` (`planned`, M6) | the Evidence dashboards build from the marts |

## Documentation

- `docs/decisions/` — ADRs for every non-obvious choice
- `docs/how-it-was-built.md`, `docs/runbook.md`, `docs/data-dictionary.md`,
  `docs/redshift-migration.md`, `docs/future-work.md` — `planned`, land with their milestones

## License

MIT
