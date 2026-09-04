---
title: Fan Unification Platform
---

One warehouse view of a fictional national soccer federation's fans, unified
across CRM, ticketing, merch, and email marketing by a measured
identity-resolution pipeline. **All data is synthetic** (seeded generator, no
real persons) — which is exactly what makes the [unification accuracy](/unification)
measurable against ground truth.

> **New here?** [Start the three-minute record-lineage tour](/start) to follow
> one generated source identity through matching, a golden record, SCD history,
> a warehouse fact, and a BI-ready mart row—with direct links to the code and SQL.

```sql summary
select * from fanuni.unification_summary
```

<BigValue data={summary} value=unified_fans title="Unified fans" fmt="#,##0" />
<BigValue data={summary} value=source_records title="Source records" fmt="#,##0" />
<BigValue data={summary} value=records_per_fan title="Records per fan" />
<BigValue data={summary} value=multi_source_fans title="Multi-source fans" fmt="#,##0" />

```sql eval_full_latest
select pair_precision, pair_recall, pair_f1, review_band
from fanuni.linkage_eval
where variant = 'full'
qualify row_number() over (order by id desc) = 1
```

<BigValue data={eval_full_latest} value=pair_precision title="Pair precision" fmt="0.0%" />
<BigValue data={eval_full_latest} value=pair_recall title="Pair recall" fmt="0.0%" />
<BigValue data={eval_full_latest} value=pair_f1 title="Pair F1" fmt="0.0%" />
<BigValue data={eval_full_latest} value=review_band title="Pairs sent to review" fmt="#,##0" />

Measured against generator ground truth on every run — including the result
that didn't flatter: at the naive threshold the probabilistic pass **lost** to
plain deterministic rules, and the committed sweep that chose the operating
point is published in full. [Baseline vs probabilistic, head to head →](/unification)

## Revenue across every pillar

Ticketing, merch, memberships, and donations live in four different source
systems; only unified identity makes one revenue picture possible.

```sql revenue
select * from fanuni.monthly_revenue
```

<BarChart
  data={revenue}
  x=month
  y=revenue
  series=pillar
  type=stacked
  title="Monthly revenue by pillar"
  yFmt="usd0"
/>

## Ticket → merch crossover

Of fans whose first ticket purchase fell in a month, the share who bought
merch within 90 days — the cross-sell question unification exists to answer.
Fans without a complete 90-day observation window are excluded, so the tail
is censored honestly instead of reading as zero conversion.

```sql crossover
select *, conversion_pct / 100.0 as conversion_rate from fanuni.crossover
```

<LineChart
  data={crossover}
  x=cohort_month
  y=conversion_rate
  yFmt="pct1"
  title="Merch conversion within 90 days of first ticket"
/>

## Explore

- [Start here: one record's lineage](/start) — source row to BI-ready result
- [Unification quality](/unification) — measured precision/recall vs ground truth
- [Revenue](/revenue) · [Engagement](/engagement) · [Pipeline ops](/ops)
