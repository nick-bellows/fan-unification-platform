# How it was built

One consolidated walkthrough, one milestone per section. ADRs in
`docs/decisions/` hold the why for each non-obvious choice.

## M0 — Scaffold

Repo, compose stack (Postgres 16, MinIO, Prefect 3 server, mock Salesforce),
typed Python package, and CI green on the empty scaffold — lint, mypy, unit
tests, docker build, gitleaks all gating from commit one.

## M1 — Synthetic sources with ground truth

A seeded generator builds ~5k true fans (households, nicknames, diacritics,
email changes over time), then projects them into four source systems with a
tagged mess taxonomy — 11 corruption types, each recorded per record in
`data/truth/record_map.csv`. The pipeline never reads the truth; only the
eval harness does. The mock Salesforce API speaks the real protocol shape
(OAuth client-credentials, SOQL with `SystemModstamp` watermarks,
`nextRecordsUrl` pagination), so the extractor is written against a faithful
interface, not a file stub. Determinism is tested by content hash.

## M2 — Extract and load

Prefect flows land everything in the MinIO lake via real `boto3` first, then
COPY into JSONB `raw` tables. Idempotency is structural: file loads are
delete+insert keyed on source file with a sha256 registry to skip unchanged
files; CRM extraction is watermark-incremental. Rows failing their pandera
contract quarantine with reasons; a whole-file contract failure is how
unexpected schema drift surfaces (the known merch drift is handled). Every
run and load audits to `ops`.

**Bug the integration suite caught:** regenerating a smaller dataset left
stale month-files from a larger earlier run in the dropzone (fewer fixtures →
some months unwritten), inflating loads by 68%. Fix: the generator owns and
clears its output dirs. The lesson is the house rule — run the checks for
real; the unit suite alone was green.

## M3 — Warehouse transforms

A ~90-line runner executes ordered SQL models (staging → core → marts) with
row counts and durations audited per model — the understanding-first
alternative to dbt (ADR 0003). Staging types, normalizes, and dedupes;
`identity_records` unifies four source shapes into the matcher's single
input. The star schema hangs off an SCD2 `dim_fan` (hybrid type-1/type-2,
ADR 0005); `fact_email_engagement` demonstrates the incremental pattern once,
deliberately. Data-quality checks are SQL files returning violating rows —
severity in the filename, results in `ops.dq_results`, error-severity
failures fail the run. The gate is itself tested by breaking an invariant and
watching it fail.

**Bug the integration suite caught:** the test connection idled in
transaction, its AccessShare locks deadlocking the transform's DROP TABLEs —
found via `pg_stat_activity`, fixed with autocommit on the test fixture.

## M4 — Unification, measured

Deterministic pass (email exact; phone+surname) through union-find, then
Splink 4 on DuckDB (ADR 0004) with folded/canonicalized names, EM-trained,
seeded for reproducibility. High-confidence pairs merge; the 0.5–0.9 band
goes to clerical review. fan_ids derive from the minimum member ref, so
stable clusters keep their ids across runs.

The eval harness scores both variants against ground truth on every CI run,
and it caught something the small dataset hid: **at the initial 0.90
threshold, the probabilistic pass lost to the plain deterministic baseline on
F1 at full scale** (0.874 vs 0.889) — precision collapsed to 0.778 because
household and name+geography false positives score above 0.999
(Fellegi-Sunter posteriors saturate when many fields agree). The response was
not to retune quietly but to measure the operating curve: a committed
threshold sweep (`eval/results/threshold_sweep.md`, reproducible via
`fanuni evaluate --sweep`) showed the useful separation lives above 0.999,
and the v3 operating point (0.9999) beats the baseline on recall (+3.1 pts)
and F1 (+1.4 pts) at equal precision, with 3,376 uncertain pairs routed to
clerical review. The recall gains are exactly where exact rules are blind
(changed emails, typos); the version bump and regenerated reports landed in
one commit, per the eval-honesty rule. CI enforces metric floors set just
below observed values.

## M5 — Production ops

Nightly scheduled workflow runs the full-size pipeline end-to-end and
uploads the run report + eval results as artifacts; retries with backoff on
network tasks; a one-page runbook covers backfills, drift, quarantine triage,
and review-band handling. Terraform for the real AWS deployment (S3 +
Redshift Serverless + COPY role) validates in CI and is deliberately never
applied ($0 rule); `warehouse/redshift/` + `docs/redshift-migration.md`
carry the dialect differences. Column-level grants keep PII from the analyst
role — and a test proves the denial.

The performance pass came from the audit trail: `ops.model_runs` showed the
crossover mart at 10× the next slowest model; `EXPLAIN ANALYZE` blamed a
correlated `EXISTS` (2,724 sequential scans of the merch fact, ~14M row
visits). Rewritten as a hash join after a row-for-row equivalence check:
506 ms → 3.6 ms, model build 2,048 ms → 82 ms (ADR 0006).

## M6 — Dashboards and packaging

Evidence.dev builds the dashboard site from the marts in CI — the stack
comes up, the pipeline runs, and only then does Evidence extract — so the
published page is provably the pipeline's output. Deployed to GitHub Pages.
