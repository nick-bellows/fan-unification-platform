-- SCD2 invariant: exactly one current version per fan_id.
SELECT fan_id, count(*)
FROM core.dim_fan
WHERE is_current
GROUP BY fan_id HAVING count(*) > 1
