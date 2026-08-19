SELECT run_id, flow_name, status, started_at, finished_at,
       round(extract(epoch FROM (finished_at - started_at))::numeric, 1) AS seconds
FROM ops.pipeline_runs ORDER BY started_at DESC LIMIT 50
