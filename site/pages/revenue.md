---
title: Revenue
---

```sql monthly
select * from fanuni.monthly_revenue
```

<BarChart
  data={monthly}
  x=month
  y=revenue
  series=pillar
  type=stacked
  title="Monthly revenue by pillar"
  yFmt="usd0"
/>

## By match

```sql matches
select * from fanuni.revenue_by_match
```

```sql matches_sold
select * from ${matches} where ticket_revenue > 0
```

<BarChart
  data={matches_sold}
  x=match_id
  y=ticket_revenue
  title="Ticket revenue by match"
  yFmt="usd0"
/>

<DataTable data={matches} rows=15 search=true>
  <Column id=match_date />
  <Column id=home_team />
  <Column id=away_team />
  <Column id=venue />
  <Column id=competition />
  <Column id=orders fmt="#,##0" />
  <Column id=seats_sold fmt="#,##0" />
  <Column id=ticket_revenue fmt="usd0" />
  <Column id=unique_buyers fmt="#,##0" />
</DataTable>

## Ticket → merch cohorts

Cohorts without a complete 90-day observation window are excluded (censored,
not counted as zero conversion).

```sql crossover
select * from fanuni.crossover
```

<DataTable data={crossover}>
  <Column id=cohort_month />
  <Column id=new_ticket_fans fmt="#,##0" />
  <Column id=bought_merch_within_90d fmt="#,##0" />
  <Column id=conversion_pct fmt="0.0'%'" />
</DataTable>
