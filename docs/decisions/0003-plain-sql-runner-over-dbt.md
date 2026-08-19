# ADR 0003: Plain SQL + Python transform runner, not dbt

**Status:** accepted · **Date:** 2026-08-19

## Context

The staging → star-schema → marts layer needs ordered, tested, documented SQL.
dbt-core is the industry default and was considered.

## Decision

A small hand-built runner (`fanuni.pipeline.sql_runner`) executes a manifest of
ordered SQL model files inside transactions, records row counts to `ops`
tables, and runs SQL assertion checks with `error|warn` severity.

Chosen because (a) the job description names Python and SQL, not dbt — the
transform layer should demonstrate those directly; (b) building the
mini-framework shows understanding of what dbt automates (ordering,
idempotency, testing, audit) rather than familiarity with its CLI; (c) one
fewer toolchain in a repo that already carries Prefect, Splink, and Evidence.

## Consequences

- Every model must be written idempotently by hand; the runner enforces
  nothing a test doesn't check.
- No free lineage graph or docs site; the data dictionary is maintained by
  hand in `docs/data-dictionary.md`.
- Migrating the models to dbt later is mechanical (each model file is already
  a single SELECT-shaped statement per table).
