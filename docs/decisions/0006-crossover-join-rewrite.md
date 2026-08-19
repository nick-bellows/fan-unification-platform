# ADR 0006: Crossover mart rewritten from correlated EXISTS to a hash join

**Status:** accepted · **Date:** 2026-08-19

## Context

At full scale (5k fans), `ops.model_runs` showed
`ticket_to_merch_crossover` at 2,177 ms — 10× the next slowest model.
`EXPLAIN ANALYZE` attributed it to the correlated `EXISTS` subquery: a
sequential scan of `fact_merch_sales` executed once per ticket-buying fan
(2,724 loops × ~5.2k rows ≈ 14M row visits; 506 ms for the query alone).

## Decision

Rewrite the conversion test as a `LEFT JOIN` with the 90-day window in the
join condition and `count(ms.fan_key) > 0` per group. One hash join replaces
2,724 scans.

Measured on identical data: **506 ms → 3.6 ms**, with a row-for-row
equivalence check (zero disagreements) before the swap.

## Consequences

- The join shape is also what Redshift wants: with both facts DISTKEY'd on
  `fan_key` the join is co-located, while a correlated subquery pattern
  would broadcast.
- General lesson recorded for the model layer: per-row subqueries against
  fact tables don't survive scale; prefer joins the planner can hash.
