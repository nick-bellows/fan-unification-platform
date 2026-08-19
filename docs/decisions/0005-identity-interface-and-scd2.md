# ADR 0005: The identity interface, stable fan_ids, and hybrid SCD

**Status:** accepted · **Date:** 2026-08-19

## Context

Unification improves over milestones (deterministic in M3, +Splink in M4,
threshold tuning later). The SQL model layer must not change every time the
matcher does, and `dim_fan` should carry meaningful history across runs.

## Decision

1. **Interface tables.** The unifier fully rebuilds exactly two tables —
   `identity.fan_xref` (record → fan) and `identity.golden_fans` (survived
   attributes) — and the SQL layer only ever reads them. Swapping matcher
   internals touches zero SQL models.
2. **Stable fan_ids.** `fan_id = "FAN-" + sha1(min(member refs))`: a cluster
   that doesn't change keeps its id across runs; union-find roots tie-break
   to the smallest ref for the same reason.
3. **Hybrid SCD on `core.dim_fan`.** Type 2 (versioned) for identity
   attributes — name, email, phone, city/state/zip, dob; type 1 (updated in
   place) for activity attributes — `sources`, `record_count` — which grow on
   nearly every load and would churn meaningless versions.
4. **Survivorship**: latest-observed email (people move forward), modal value
   for names/phone/location (folded comparison, ties to longest), CRM-first
   DOB (only full-date source).

## Consequences

- A re-shaped cluster (e.g. Splink joins two previously separate fans) is a
  *new* fan_id; the old ids' versions get retired, not rewritten — history
  stays truthful about what the warehouse believed when.
- Facts join through xref → current dim_fan row each rebuild, so they always
  reflect current identity; the incremental `fact_email_engagement` is the
  documented exception (see the model header).
