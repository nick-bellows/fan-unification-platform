---
title: Start Here — One Record's Lineage
---

This three-minute tour follows one **synthetic** fan across the actual pipeline
output. The selected cluster is chosen by SQL from the current generated build
and is **verified against generator ground truth as exactly one person** —
names, identifiers, match evidence, warehouse keys, totals, and that
verification are not typed into this page. (What a cluster looks like when
the matcher gets it *wrong* is shown further down, on purpose.)

> **Choose a path:** Data engineers can follow the six numbered stages below.
> Analytics consumers can jump to [the BI-ready result](#6-consume-the-bi-ready-row).

## 1. Land and validate source records

The pipeline extracts a Salesforce-shaped API plus ticketing, merchandise, and
email files into an S3-compatible landing zone. Pandera contracts normalize
valid records and quarantine invalid rows with reasons.

[Prefect flow](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/pipeline/flows.py) ·
[contracts](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/pipeline/contracts.py) ·
[quarantine loader](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/pipeline/load.py)

## 2. Compare identity evidence

```sql trace_records
select * from fanuni.record_trace
```

<DataTable data={trace_records} rows=10 search=true>
  <Column id=source_system />
  <Column id=source_record_id />
  <Column id=observed_name />
  <Column id=observed_email />
  <Column id=observed_phone />
  <Column id=observed_zip />
  <Column id=cluster_method />
  <Column id=probabilistic_score fmt="0.000000" />
  <Column id=match_evidence />
</DataTable>

```sql tour_truth
select
  max(true_entity_count) as true_entities,
  max(cluster_member_count) as members
from ${trace_records}
```

**Ground-truth check:** these <Value data={tour_truth} column=members /> source
records belong to <Value data={tour_truth} column=true_entities /> true
identity — verified against ground truth at build time by the evaluation
harness, the only component allowed to read it.

`match_evidence` is derived from the normalized source rows and the persisted
cluster method. A deterministic cluster can contain transitive edges, so the
table does not invent a pair-level reason when the current model does not retain
one. Probabilistic records show the retained score; ambiguous pairs below the
auto-merge threshold go to manual review instead of this cluster.

[deterministic rules](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/unification/deterministic.py) ·
[probabilistic matcher](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/unification/probabilistic.py) ·
[threshold evidence](https://github.com/nick-bellows/fan-unification-platform/blob/main/eval/results/threshold_sweep.md)

## 3. Resolve the golden identity

The unifier writes the source-to-fan cross-reference and applies deterministic
survivorship rules. Stable cluster membership produces a stable `fan_id`.

[golden-record implementation](https://github.com/nick-bellows/fan-unification-platform/blob/main/src/fanuni/unification/golden.py) ·
[identity schema](https://github.com/nick-bellows/fan-unification-platform/blob/main/warehouse/ddl/0004_identity.sql)

## 4. Preserve dimension history

```sql trace_warehouse
select * from fanuni.warehouse_trace
```

<DataTable data={trace_warehouse} rows=10>
  <Column id=fan_id />
  <Column id=fan_key />
  <Column id=canonical_name />
  <Column id=canonical_email />
  <Column id=sources />
  <Column id=record_count />
  <Column id=valid_from />
  <Column id=valid_to />
  <Column id=is_current contentType=boolean />
</DataTable>

Identity attributes use SCD2 history; activity attributes update in place so a
new purchase does not create a meaningless identity version.

[SCD model](https://github.com/nick-bellows/fan-unification-platform/blob/main/warehouse/models/30_core/20_dim_fan.sql) ·
[design decision](https://github.com/nick-bellows/fan-unification-platform/blob/main/docs/decisions/0005-identity-interface-and-scd2.md)

## 5. Join a warehouse fact

```sql trace_activity
select * from fanuni.activity_trace
```

<DataTable data={trace_activity} rows=10>
  <Column id=order_id />
  <Column id=fan_key />
  <Column id=match_id />
  <Column id=match_date />
  <Column id=home_team />
  <Column id=away_team />
  <Column id=channel />
  <Column id=seats />
  <Column id=ticket_revenue fmt="usd0" />
</DataTable>

[ticket fact model](https://github.com/nick-bellows/fan-unification-platform/blob/main/warehouse/models/30_core/30_fact_ticket_sales.sql) ·
[referential-integrity check](https://github.com/nick-bellows/fan-unification-platform/blob/main/warehouse/checks/error__fact_tickets_match_fk.sql)

## 6. Consume the BI-ready row

```sql trace_mart
select
  canonical_name,
  sources,
  ticket_orders,
  ticket_revenue,
  merch_orders,
  merch_revenue,
  email_sends,
  email_opens,
  total_revenue
from fanuni.warehouse_trace
where is_current
```

<DataTable data={trace_mart}>
  <Column id=canonical_name />
  <Column id=sources />
  <Column id=ticket_orders />
  <Column id=ticket_revenue fmt="usd0" />
  <Column id=merch_orders />
  <Column id=merch_revenue fmt="usd0" />
  <Column id=email_sends />
  <Column id=email_opens />
  <Column id=total_revenue fmt="usd0" />
</DataTable>

[Fan 360 mart](https://github.com/nick-bellows/fan-unification-platform/blob/main/warehouse/models/40_marts/10_fan_360.sql) ·
[data dictionary](https://github.com/nick-bellows/fan-unification-platform/blob/main/docs/data-dictionary.md) ·
[pipeline operations](/ops) · [measured linkage quality](/unification)

## Anatomy of a false merge

The matcher is measured, not perfect — and the dominant failure mode deserves
the same visibility as the success story. This is the **largest cluster the
ground truth says is wrong**: its records belong to more than one real
(generated) person, merged because a household shares one email address.

```sql false_merge
select * from fanuni.false_merge_trace
```

```sql false_merge_summary
select max(member_count) as members, max(true_entity_count) as true_entities
from ${false_merge}
```

<Value data={false_merge_summary} column=members /> records, but
<Value data={false_merge_summary} column=true_entities /> distinct true
identities behind them:

<DataTable data={false_merge} rows=12>
  <Column id=source_system />
  <Column id=source_record_id />
  <Column id=observed_name />
  <Column id=observed_email />
  <Column id=cluster_method />
</DataTable>

Shared household emails are the measured top false-positive source
(see [recall by mess type](/unification#recall-by-injected-mess-type)); the
review band exists so ambiguous pairs go to a human queue instead of merging,
and household modeling is the roadmap's next evidence-led experiment. Hiding
this cluster would contradict the evaluation this project publishes.

## Trust boundary

- Every displayed person and transaction is deterministically generated and fictional.
- The featured cluster is verified pure against ground truth at build time; if no verified cluster exists, the site build fails rather than showing an unlabeled one.
- CI rebuilds the source systems, pipeline, warehouse, and site together.
- PostgreSQL and MinIO prove the local interfaces; Redshift and S3 remain a documented, validate-only deployment design.
- The first probabilistic threshold performed worse than deterministic rules. That result remains visible rather than being removed from the story.
