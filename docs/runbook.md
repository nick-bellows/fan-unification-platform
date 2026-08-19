# Runbook

One page: how to operate this pipeline and what to do when it breaks.

## Normal operation

The nightly GitHub Actions workflow (`nightly-pipeline`) generates the
full-size dataset, runs `fanuni pipeline` (ingest → transform → unify →
quality gates) and `fanuni evaluate`, and uploads the run report + eval
results as artifacts. A failure fails the workflow — that's the alert.

Where to look, in order:

1. **Actions run log/artifacts** — `nightly_run.json` has per-source counts.
2. **`ops` schema** — `pipeline_runs` (status per flow), `load_audit` (rows
   in/rejected per object), `dq_results` (which check, how many rows, detail),
   `model_runs` (rows + duration per model).
3. **Prefect UI** (`http://localhost:4200` in the compose stack) — task-level
   retries and logs.

## Common tasks

| Task | Command |
| --- | --- |
| Backfill one window | `fanuni ingest --source files --start-month 2025-01 --end-month 2025-03 --force` |
| Force-reload every file | `fanuni ingest --source files --force` |
| Re-extract all of Salesforce (ignore watermark) | `fanuni ingest --source crm --full-refresh` |
| Rerun one model | `fanuni transform --select fan_360` |
| Rerun unification only | `fanuni unify` (then `fanuni transform` for downstream models) |
| Regenerate eval reports | `fanuni evaluate` |

Reloads are always safe: file loads are delete+insert keyed on the source
file, and re-extracting the CRM re-lands versions that staging dedupes by
`SystemModstamp`.

**Rebuilding the two incremental tables** (needed if unification reshapes
clusters and you want history to reflect it):
`DROP TABLE core.fact_email_engagement;` and/or `DROP TABLE core.dim_fan;`
then `fanuni transform`. Dropping `dim_fan` discards SCD2 history — deliberate
decision, not routine maintenance.

## Failure triage

- **A source is down** — extract tasks retry 3× with backoff, then the flow
  fails and `ops.pipeline_runs` shows `failed`. Fix the source, rerun
  `fanuni ingest`; the watermark/sha registry means only missing work repeats.
- **Rows in quarantine** — `SELECT reason, count(*) FROM raw.quarantine GROUP
  BY reason`. A handful of rows: upstream data bug; the load continued without
  them. A whole file (`column_in_dataframe` reason): schema drift — teach the
  contract and staging model the new shape (see the merch drift handling in
  `30_stg_merch_order_items.sql`), then `--force` reload that file.
- **Quality gate failed** — `SELECT * FROM ops.dq_results WHERE NOT passed
  ORDER BY checked_at DESC`. `detail` holds sample violating rows. Error
  checks mean downstream data is wrong: fix, rerun `fanuni transform && fanuni
  dq` before trusting marts.
- **Review-band pairs** (`data/review/review_pairs.csv`) — possible matches
  Splink scored between the review and auto-merge thresholds. A human
  accepts/rejects; accepted pairs belong in the deterministic rules or as
  threshold evidence — never hand-edit `identity.fan_xref`.

## Adding a source

1. Generator emits it (`fanuni/generator/sources.py`) with truth records.
2. Contract in `pipeline/contracts.py`, entry in `FILE_SOURCES`/`RAW_TABLES`,
   raw table in `warehouse/ddl/0003_raw.sql`.
3. Staging model + `identity_records` union branch if identity-bearing.
4. DQ checks + eval rerun (`fanuni evaluate`) to see the linkage impact.
