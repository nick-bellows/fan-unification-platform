DROP TABLE IF EXISTS staging.stg_email_campaigns;
CREATE TABLE staging.stg_email_campaigns AS
SELECT
  payload->>'campaign_id'                    AS campaign_id,
  payload->>'name'                           AS name,
  (payload->>'sent_at')::timestamptz         AS sent_at
FROM raw.email_campaigns;
