DROP TABLE IF EXISTS staging.stg_email_subscribers;
CREATE TABLE staging.stg_email_subscribers AS
WITH ranked AS (
  SELECT payload, loaded_at,
         row_number() OVER (
           PARTITION BY payload->>'subscriber_id' ORDER BY loaded_at DESC
         ) AS rn
  FROM raw.email_subscribers
)
SELECT
  payload->>'subscriber_id'                  AS subscriber_id,
  lower(btrim(payload->>'email'))            AS email,
  initcap(btrim(payload->>'first_name'))     AS first_name,
  initcap(btrim(payload->>'last_name'))      AS last_name,
  (payload->>'signup_date')::date            AS signup_date,
  payload->>'status'                         AS status,
  nullif(payload->>'birth_year', '')::int    AS birth_year,
  left(nullif(payload->>'zip', ''), 5)       AS zip
FROM ranked
WHERE rn = 1;
