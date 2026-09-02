# Interview Guide

This guide anchors discussion to the implementation and retained evidence. The platform uses
synthetic data, runs locally/in CI, and has not operated against production Salesforce, S3,
Redshift, or personal data. PostgreSQL and MinIO are documented local substitutes; Terraform
is validate-only and has never been applied.

For the shorter metrics-focused walkthrough, see [interview-brief.md](interview-brief.md).

## Architecture in one minute

Four synthetic systems—a Salesforce-shaped CRM API, ticketing, merchandise, and email—flow
through real Prefect tasks into an S3-compatible MinIO landing zone. Contract validation sends
bad records to a reason-coded quarantine before JSONB raw tables. Ordered SQL models normalize
the sources, build an identity interface, create a hybrid SCD2 fan dimension and facts, then
publish BI marts. Identity resolution compares deterministic rules with a seeded Splink
Fellegi-Sunter pass against generator ground truth. CI enforces data-quality and linkage floors,
and the Evidence site is built only from a completed pipeline run.

## Where to point an interviewer

| Requirement | Evidence |
| --- | --- |
| Prefect orchestration and retries | `src/fanuni/pipeline/flows.py` |
| Salesforce-style extraction | `src/fanuni/pipeline/salesforce.py`, `salesforce_mock/app.py` |
| S3-compatible landing | `src/fanuni/pipeline/lake.py` |
| Contracts and quarantine | `pipeline/contracts.py`, `pipeline/load.py`, ingest integration tests |
| Incremental/idempotent behavior | `pipeline/load.py`, `tests/integration/test_transform.py` |
| Deterministic identity rules | `unification/deterministic.py` |
| Probabilistic linkage and review band | `unification/probabilistic.py` |
| Ground-truth evaluation | `unification/evaluate.py`, `eval/results/linkage_eval.md` |
| Relational/dimensional modeling | `warehouse/models/30_core`, `warehouse/models/40_marts` |
| SCD behavior and stable keys | `unification/golden.py`, ADR 0005 |
| SQL data-quality gates | `warehouse/checks`, `pipeline/quality.py` |
| Operations and lineage | `warehouse/ddl/0002_ops.sql`, `docs/runbook.md` |
| Redshift migration boundary | `warehouse/redshift`, `docs/redshift-migration.md` |
| CI and scheduled operation | `.github/workflows/ci.yml`, `nightly.yml`, `site.yml` |

## Important tradeoffs

### PostgreSQL and MinIO instead of live AWS

The project exercises relational SQL and the S3 API without incurring a standing cloud bill.
Redshift differences—COPY syntax, SUPER, constraints, distribution, sort keys, and maintenance—
are isolated in a migration document and Redshift DDL. This proves local behavior and design
reasoning, not Redshift runtime performance or AWS operation.

### Plain SQL runner instead of dbt

The repository exposes model ordering, transactions, row-count audit, severity-tagged tests,
and idempotency directly. It avoids another framework in a stack that already includes Prefect,
Splink, and Evidence. The cost is manual lineage/documentation and fewer built-in deployment
features. ADR 0003 records the decision.

### Deterministic rules before probabilistic linkage

Exact normalized identifiers are explainable and establish a baseline. Splink adds links when
exact evidence is absent, but every threshold is evaluated against synthetic truth. The first
0.90 operating point reduced F1; that negative result was retained. Version 3 at 0.9999 improves
recall/F1, but precision remains about 0.85—far below a responsible unattended-merge boundary.
Probabilistic links would remain behind clerical review or require stronger evidence.

### Stable identity interface

`identity.fan_xref` and `identity.golden_fans` isolate matcher changes from warehouse SQL.
Stable IDs derive from cluster members, and the hybrid SCD versions identity attributes while
updating activity attributes in place. A reshaped cluster receives a new ID so history records
what the warehouse believed at the time.

## Hard problems actually solved

- Generated realistic cross-system identity errors while retaining hidden truth solely for
  evaluation; runtime pipeline code never reads truth labels.
- Made file reprocessing safe with hash registration and keyed replacement, while keeping one
  fact incrementally append-only with a `NOT EXISTS` guard.
- Quarantined row-level contract failures with reasons and handled one known schema rename in
  staging without leaking drift into downstream models.
- Kept deterministic edges when the probabilistic pass adds links, with seeded training for
  reproducible clusters.
- Tested SCD2 version stability, source-to-fact reconciliation, foreign keys, uniqueness,
  freshness, and a repeated-run no-op against real Docker services.
- Published the pipeline's actual dashboard outputs rather than hand-entered metrics.

## Likely questions

### Why is a matcher with 0.8485 precision useful?

It is useful as a measured reference implementation, not as an autonomous merge policy.
Precision exposes a household/shared-email failure mode that aggregate fan counts would hide.
The responsible next step is stronger discriminating evidence and human review—not relabeling
the result as production-ready.

### How are late arrivals and backfills handled?

File sources can be loaded for an explicit month window and forced safely because replacement
is keyed to source file. CRM extraction uses a watermark/full-refresh boundary. Models rebuild
idempotently; integration tests include late arrivals and a repeated-run no-op. The runbook
contains the exact operational commands and the known full-dataset replacement procedure.

### What happens on schema drift?

Raw payloads remain JSONB. Rows that fail a known contract enter `raw.quarantine` with the
source file and reason; a whole-file contract change fails visibly. Once the contract/staging
model is updated, a forced reload replaces stale quarantine rows rather than accumulating them.

### How do data consumers know a mart is trustworthy?

Error-severity SQL assertions fail the flow, while warnings remain visible in `ops.dq_results`.
Checks cover source reconciliation, uniqueness, referential integrity, xref coverage, one
current SCD row, freshness, and quarantine rate. CI builds the dashboard only after a real
pipeline and those gates finish.

### What would change on Redshift?

The landing interface remains S3/boto3. Loads become Redshift `COPY` from S3, JSONB becomes
SUPER where appropriate, and Postgres indexes/constraints give way to distribution/sort design
plus explicit quality enforcement. Those mappings are documented; performance remains
unverified until an approved ephemeral deployment is measured.

## Failure scenarios

| Failure | Implemented behavior | Production follow-up |
| --- | --- | --- |
| Source/API unavailable | Prefect retry/backoff, failed run in `ops.pipeline_runs` | Alert routing, SLOs, source-specific circuit policy |
| Invalid row | Reason-coded quarantine; valid rows continue | Steward queue, SLA, source-owner feedback |
| Unknown file schema | Contract failure instead of silent coercion | Schema registry/version negotiation |
| Quality assertion fails | Error check fails the pipeline | Prevent downstream publish and page on-call |
| Ambiguous identity pair | Review-band export; no auto-merge | Audited review UI and labeled decisions |
| Bad linkage threshold | Versioned evaluation/regression floors | Separate train/validation/time-based evaluation |
| Cluster changes | New stable ID and retired SCD history | Durable merge/split lineage and downstream remapping |
| Warehouse scale exceeds memory | Current Splink/DuckDB design becomes unsuitable | Warehouse/Spark backend and partitioned blocking |

## Improvements with more time or approved cloud access

1. Add an audited clerical-review workflow and feed reviewed labels into a separate evaluation
   set without tuning repeatedly on the committed 5,000-entity fixture.
2. Model households and stronger identifiers to address the dominant shared-email false merges.
3. Add schema-version contracts and source freshness SLAs.
4. Exercise an ephemeral Redshift deployment, retain query/load evidence, then destroy it under
   a pre-approved budget; until then keep AWS claims design-only.
5. Add merge/split lineage and downstream re-keying for identity-cluster changes.
6. Replace the current transitive Evidence/Svelte build tree when upstream releases resolve its
   outstanding audit findings; do not force an unsafe dependency downgrade merely for a badge.
