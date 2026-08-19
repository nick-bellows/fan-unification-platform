# ADR 0004: Splink 4 on DuckDB for the probabilistic pass

**Status:** accepted · **Date:** 2026-08-19

## Context

The deterministic rules cannot link records with no exact key in common (a
changed email, a typo'd surname with a different phone format). Probabilistic
record linkage (Fellegi-Sunter) is the standard answer; Splink is the
production-grade open-source implementation (UK Ministry of Justice), with
EM parameter training and blocking built in. No LLM involved — this is
classical statistics, allowed under the house rules.

The warehouse is Postgres, but Splink's first-class, best-tested backend is
DuckDB; its Postgres backend is secondary.

## Decision

Run Splink in-process on DuckDB over a pandas projection of
`staging.identity_records` (folded names, canonical nicknames, birth year).
Scored pairs above the auto-merge threshold join the deterministic edges in
one union-find; results are written back to `identity.fan_xref` /
`identity.golden_fans` like any other unifier output. Pairs between the
review and auto-merge thresholds go to a clerical-review CSV, not into
clusters.

u-estimation is seeded (`UnifyConfig.seed`) so reruns produce identical
clusters — required for the SCD2 stability tests.

## Consequences

- The unification step needs records in memory (~fine at 10^4–10^5 records;
  at USSF-real scale you'd point Splink at the warehouse backend or Spark).
- Two engines in one pipeline (Postgres + DuckDB), confined to one module.
- Thresholds are eval-versioned: changing them bumps `UNIFIER_VERSION` and
  lands with regenerated `eval/results/` in the same commit.
