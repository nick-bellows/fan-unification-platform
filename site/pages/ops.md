---
title: Pipeline Ops
---

Every flow run, load, model build, and quality check writes to the `ops`
schema; this page is that audit trail.

## Data-quality gates

```sql dq
select * from fanuni.dq_results
```

<DataTable data={dq}>
  <Column id=check_name />
  <Column id=severity />
  <Column id=passed contentType=boolean />
  <Column id=failed_rows fmt="#,##0" />
  <Column id=checked_at />
</DataTable>

## Recent flow runs

```sql runs
select * from fanuni.pipeline_runs
```

<DataTable data={runs} rows=15>
  <Column id=flow_name />
  <Column id=status />
  <Column id=started_at />
  <Column id=seconds fmt="#,##0.0" />
</DataTable>

## Loads by source

```sql loads
select * from fanuni.load_audit
```

<DataTable data={loads}>
  <Column id=source />
  <Column id=objects fmt="#,##0" />
  <Column id=rows_loaded fmt="#,##0" />
  <Column id=rows_rejected fmt="#,##0" />
  <Column id=last_loaded_at />
</DataTable>

## Model build times (latest run)

```sql models
select * from fanuni.model_runs
```

<BarChart data={models} x=model y=duration_ms swapXY=true title="Model duration (ms)" />
