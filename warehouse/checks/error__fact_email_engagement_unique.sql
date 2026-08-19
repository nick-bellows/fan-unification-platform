-- The incremental fact must never double-load an event.
SELECT event_id, count(*)
FROM core.fact_email_engagement
GROUP BY event_id HAVING count(*) > 1
