-- Latest run per model
SELECT DISTINCT ON (model)
  model, schema_name, rows, duration_ms, executed_at
FROM ops.model_runs
ORDER BY model, executed_at DESC
