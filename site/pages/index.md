---
title: Fan Unification Platform
---

One warehouse view of a fictional national soccer federation's fans, unified
across CRM, ticketing, merch, and email marketing by a measured
identity-resolution pipeline. **All data is synthetic** (seeded generator, no
real persons) — which is exactly what makes the [unification accuracy](/unification)
measurable against ground truth.

```sql summary
select * from fanuni.unification_summary
```

<BigValue data={summary} value=unified_fans title="Unified fans" fmt="#,##0" />
<BigValue data={summary} value=source_records title="Source records" fmt="#,##0" />
<BigValue data={summary} value=records_per_fan title="Records per fan" />
<BigValue data={summary} value=multi_source_fans title="Multi-source fans" fmt="#,##0" />

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

- [Unification quality](/unification) — measured precision/recall vs ground truth
- [Revenue](/revenue) · [Engagement](/engagement) · [Pipeline ops](/ops)
