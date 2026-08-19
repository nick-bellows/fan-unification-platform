-- Engagement events referencing a subscriber the platform never delivered.
SELECT e.event_id, e.subscriber_id
FROM staging.stg_email_events e
LEFT JOIN staging.stg_email_subscribers s ON s.subscriber_id = e.subscriber_id
WHERE s.subscriber_id IS NULL
LIMIT 50
