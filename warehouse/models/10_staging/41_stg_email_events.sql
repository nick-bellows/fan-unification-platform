DROP TABLE IF EXISTS staging.stg_email_events;
CREATE TABLE staging.stg_email_events AS
WITH ranked AS (
  SELECT payload, loaded_at,
         row_number() OVER (
           PARTITION BY payload->>'event_id' ORDER BY loaded_at DESC
         ) AS rn
  FROM raw.email_events
)
SELECT
  payload->>'event_id'                       AS event_id,
  payload->>'subscriber_id'                  AS subscriber_id,
  payload->>'campaign_id'                    AS campaign_id,
  payload->>'event_type'                     AS event_type,
  (payload->>'occurred_at')::timestamptz     AS occurred_at
FROM ranked
WHERE rn = 1;
