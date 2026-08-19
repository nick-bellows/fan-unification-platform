# Interview brief

The walkthrough script and the questions worth being ready for. One page.

## 90-second walkthrough

Four messy source systems — a Salesforce-style CRM (spoken to over the real
protocol shape: OAuth, SOQL watermarks, pagination), ticketing, merch, and
email marketing — flow through Prefect into an S3-style lake (real boto3
against MinIO) and a Postgres warehouse modeled Redshift-consciously. The
distinctive part is unification: a deterministic pass plus a Splink
(Fellegi-Sunter) pass resolve 17k records into ~5k golden fans, and because
the synthetic generator emits ground truth, the accuracy is **measured** —
precision/recall per mess type, baseline vs probabilistic, on every CI run,
with regression floors. Downstream: an SCD2 fan dimension, a star schema, and
Evidence dashboards built in CI from a real pipeline run.

## The numbers to know (full scale: 5,000 entities, 17,487 records)

Deterministic baseline: precision 0.848 / recall 0.934 / F1 0.889. Splink at
the naive 0.90 threshold: F1 0.874 — **it lost to the baseline**, because FS
posteriors saturate and household/name-coincidence false positives score
above 0.999. The committed threshold sweep found the real operating point:
at 0.9999, precision 0.849 / recall 0.964 / F1 0.903 — beats the baseline on
both recall and F1 at equal precision, with 3,376 uncertain pairs sent to
clerical review. 5,031 unified fans against 5,000 true entities. The
"sophisticated thing initially lost, measured honestly, fixed from the
curve, published the whole story" arc is the point.

## Questions to expect

- **Why not dbt?** The JD says Python and SQL; building the runner (ordered
  models, audited row counts, severity-tagged SQL assertions) shows what dbt
  automates. Migration to dbt is mechanical — each model is already one
  statement per table. (ADR 0003)
- **Isn't picking the threshold from the eval just overfitting?** Selecting
  an operating point from a measured precision/recall curve is how record
  linkage is deployed; the dishonest version is doing it silently. Here the
  whole curve is committed, the change bumped `UNIFIER_VERSION`, and CI
  floors pin the result. The residual false positives are households sharing
  an email — the fix is better evidence (household modeling, distinct DOBs)
  or clerical review, not more threshold surgery.
- **How do you know re-runs are safe?** Structural idempotency, tested:
  delete+insert keyed on source file, sha-registry skips, watermark
  extraction, an append-only incremental fact with a NOT EXISTS guard, and an
  integration stage asserting a re-run is a no-op.
- **What breaks when a source changes its schema?** Landed anyway (JSONB
  raw), quarantined at contract level with a whole-file reason if unknown;
  the known merch rename is folded in staging so downstream never sees it.
- **How would this move to real Redshift?** COPY-from-S3 instead of streamed
  COPY, SUPER instead of JSONB, DISTKEY/SORTKEY instead of indexes — the
  divergence table is `docs/redshift-migration.md`, the DDL variants and
  Terraform are in the repo. All boto3 code targets real S3 by dropping one
  env var.
- **Where does this design not scale?** In-memory pairing at ~10^6+ records
  (move Splink to a warehouse backend/Spark); full-rebuild staging (fine at
  this volume, documented); single-node Postgres (the Redshift story).
- **What did you get wrong along the way?** Stale generator outputs inflating
  loads 68%; a test connection deadlocking the transform via an idle
  transaction; a guessed metric floor corrected by the first honest
  measurement. All three are in `docs/how-it-was-built.md`.

## Rules the repo enforces on itself

Synthetic data only, visibly labeled; no LLM in the runtime path; the
pipeline never reads ground truth (only the eval harness); metric/threshold
changes land with regenerated eval reports and a version bump; error-severity
quality gates fail CI; the published dashboard is built from a real pipeline
run in CI, never hand-fed.
