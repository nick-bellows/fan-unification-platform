SELECT source, count(*) AS objects, sum(rows_loaded) AS rows_loaded,
       sum(rows_rejected) AS rows_rejected, max(loaded_at) AS last_loaded_at
FROM ops.load_audit GROUP BY source ORDER BY source
