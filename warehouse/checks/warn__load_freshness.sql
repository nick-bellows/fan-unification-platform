-- No successful load in the last 26 hours (the nightly plus slack). Warn
-- severity: meaningful in scheduled operation, expected to trip on a repo
-- that has sat idle.
SELECT max(loaded_at) AS last_load
FROM ops.load_audit
HAVING max(loaded_at) < now() - interval '26 hours'
    OR max(loaded_at) IS NULL
