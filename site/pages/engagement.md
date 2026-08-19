---
title: Email Engagement
---

```sql campaigns
select *,
  open_rate_pct / 100.0 as open_rate,
  click_rate_pct / 100.0 as click_rate
from fanuni.campaign_engagement
```

<LineChart
  data={campaigns}
  x=sent_date
  y={["open_rate", "click_rate"]}
  yFmt="pct1"
  title="Open and click rates by campaign send date"
/>

<DataTable data={campaigns} rows=15 search=true>
  <Column id=sent_date />
  <Column id=name />
  <Column id=sends fmt="#,##0" />
  <Column id=opens fmt="#,##0" />
  <Column id=clicks fmt="#,##0" />
  <Column id=open_rate_pct fmt="0.0'%'" />
  <Column id=click_rate_pct fmt="0.0'%'" />
</DataTable>

Engagement events resolve to unified fans, so open/click behavior joins
ticketing and merch history on the [overview](/) side rather than living
in a marketing-platform silo.
