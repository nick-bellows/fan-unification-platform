---
title: Unification Quality
---

The unifier links records in two passes: exact deterministic rules (email;
phone + surname), then a probabilistic pass (Splink, Fellegi-Sunter) for links
exact rules can't see. Because the synthetic generator emits ground truth,
accuracy is **measured, not asserted** — pairwise precision/recall over
matched pairs, on every run.

```sql eval_latest
select variant, pair_precision, pair_recall, pair_f1, tp, fp, fn, review_band
from fanuni.linkage_eval
qualify row_number() over (partition by variant order by id desc) = 1
order by variant
```

```sql eval_full
select * from ${eval_latest} where variant = 'full'
```

<BigValue data={eval_full} value=pair_precision title="Precision (full)" fmt="0.00%" />
<BigValue data={eval_full} value=pair_recall title="Recall (full)" fmt="0.00%" />
<BigValue data={eval_full} value=pair_f1 title="F1 (full)" fmt="0.00%" />
<BigValue data={eval_full} value=review_band title="Review-band pairs" fmt="#,##0" />

## Baseline vs probabilistic, head to head

The deterministic pass alone is the baseline the Splink pass must beat — and
whatever the numbers say is what ships here.

```sql eval_long
select variant, 'precision' as metric, pair_precision as value from ${eval_latest}
union all
select variant, 'recall', pair_recall from ${eval_latest}
union all
select variant, 'F1', pair_f1 from ${eval_latest}
```

<BarChart
  data={eval_long}
  x=metric
  y=value
  series=variant
  type=grouped
  yFmt="0.00%"
  title="Pairwise metrics: deterministic baseline vs deterministic + Splink"
/>

<DataTable data={eval_latest}>
  <Column id=variant />
  <Column id=pair_precision fmt="0.0000" />
  <Column id=pair_recall fmt="0.0000" />
  <Column id=pair_f1 fmt="0.0000" />
  <Column id=tp fmt="#,##0" />
  <Column id=fp fmt="#,##0" />
  <Column id=fn fmt="#,##0" />
</DataTable>

## Recall by injected mess type

Every source record carries ground-truth tags for the mess applied to it
(nickname, typo, changed email, shared household email…). Recall per tag shows
exactly which failure modes each pass handles.

```sql tags
select
  tag,
  max(true_pairs) as true_pairs,
  max(case when variant = 'deterministic' then pair_recall end) as det_recall,
  max(case when variant = 'full' then pair_recall end) as full_recall,
  max(case when variant = 'full' then fp_pairs end) as full_fp_pairs
from fanuni.linkage_eval_tags
group by tag
order by tag
```

<DataTable data={tags}>
  <Column id=tag />
  <Column id=true_pairs fmt="#,##0" />
  <Column id=det_recall title="Recall (baseline)" fmt="0.00%" />
  <Column id=full_recall title="Recall (full)" fmt="0.00%" />
  <Column id=full_fp_pairs title="FP pairs (full)" fmt="#,##0" />
</DataTable>

## Cluster shape

```sql clusters
select * from fanuni.cluster_sizes
```

```sql methods
select 'deterministic' as method, deterministic_records as records from fanuni.unification_summary
union all
select 'probabilistic', probabilistic_records from fanuni.unification_summary
union all
select 'singleton', singleton_records from fanuni.unification_summary
```

<BarChart data={clusters} x=cluster_size y=fans title="Fans by records-per-cluster" />
<BarChart data={methods} x=method y=records title="Records by linking method" />

Pairs scored between the review and auto-merge thresholds go to a clerical
review file rather than into clusters — merging on maybes is how golden
records rot. Full methodology, thresholds, and the committed eval report:
`eval/results/` and ADR 0004 in the repo.
