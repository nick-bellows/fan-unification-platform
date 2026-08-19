# ADR 0001: Record architecture decisions

**Status:** accepted · **Date:** 2026-08-19

Every non-obvious choice gets a short ADR in this directory: context, decision,
consequences. ADRs are immutable once accepted; a reversal gets a new ADR that
supersedes the old one.

Four decisions were fixed at project start (user-chosen, not to be silently
revisited):

1. **Warehouse:** Postgres 16 in Docker standing in for AWS Redshift; MinIO
   provides the S3 API (ADR 0002).
2. **BI:** Evidence.dev static site deployed to GitHub Pages.
3. **Transforms:** plain SQL + Python — no dbt (ADR 0003).
4. **Repo name:** `fan-unification-platform`.

Standing rules inherited from the author's other portfolio repos: synthetic data
only, visibly labeled; no LLM anywhere in the runtime path; secrets only in env
vars; CI green before the repo is linked anywhere; evaluation honesty (metric
changes land atomically with regenerated reports; negative results are
published, not tuned away); cold-clone verification before publishing;
documentation restraint (one consolidated build walkthrough, one future-work
home, README ≤ ~350 lines).
