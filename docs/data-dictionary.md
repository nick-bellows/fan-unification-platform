# Data dictionary

PII classification: **[P]** personally identifying — withheld from the
`analyst` role (see `warehouse/grants.sql`); **[A]** activity/aggregate.

## core.dim_fan — golden fan records (SCD2 on identity attributes)

| column | type | notes |
| --- | --- | --- |
| fan_key | bigint | surrogate, one per version |
| fan_id | text | stable cluster id (`FAN-<hash>`), see ADR 0005 |
| first_name, last_name | text | **[P]** survived via modal value |
| email | text | **[P]** latest-observed wins |
| phone | text | **[P]** 10 digits |
| city, state, zip | text | **[P]** modal |
| dob | date | **[P]** CRM-sourced |
| sources | text | [A] comma-joined source systems (type-1) |
| record_count | int | [A] records in the cluster (type-1) |
| valid_from / valid_to / is_current | | SCD2 bookkeeping |

## identity.fan_xref — record-to-fan crosswalk

`(source_system, source_record_id) → fan_id`, with `method`
(deterministic / probabilistic / singleton) and `score` (match probability,
probabilistic only). Rebuilt in full by every unification run.

## Facts (grain · fan linkage via xref → current dim_fan)

| table | grain | measures |
| --- | --- | --- |
| fact_ticket_sales | ticket order | qty, unit_price, total |
| fact_merch_sales | order line item | quantity, unit_price, line_total |
| fact_giving | CRM opportunity | amount (Membership / Donation) |
| fact_email_engagement | engagement event (incremental by event_id) | event_type |

## Marts

| table | one row per | answers |
| --- | --- | --- |
| fan_360 | current fan | who is this fan across every pillar |
| revenue_by_match | fixture | ticket demand per match |
| monthly_revenue | month × pillar | revenue trend |
| ticket_to_merch_crossover | first-ticket cohort month | 90-day merch conversion |
| campaign_engagement | campaign | sends/opens/clicks + rates |
| unification_summary / cluster_sizes | snapshot | linkage shape + method mix |

## ops — the audit trail

`pipeline_runs` (flow status), `load_audit` (rows in/rejected per object),
`ingested_files` (sha registry driving idempotent re-runs), `watermarks`
(CRM incremental position), `model_runs` (rows + duration per model),
`dq_results` (every check result), `linkage_eval` / `linkage_eval_tags`
(measured accuracy, written only by the eval harness).

## Raw / staging

`raw.*`: landed payloads as JSONB + batch/source-file lineage columns;
`raw.quarantine` holds contract rejects with reasons. `staging.*`: typed,
normalized (email lowercased, phones digit-only, names case-normalized,
"LAST, FIRST" parsed), deduped within source; `staging.identity_records` is
the unifier's single input.
