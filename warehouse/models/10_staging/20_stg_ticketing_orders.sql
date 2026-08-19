-- Purchaser names arrive in three formats ("First Last", "LAST, FIRST",
-- "First M. Last"); parsing normalizes them here so downstream identity work
-- sees consistent first/last columns. initcap also undoes case mess.
DROP TABLE IF EXISTS staging.stg_ticketing_orders;
CREATE TABLE staging.stg_ticketing_orders AS
WITH ranked AS (
  SELECT payload, loaded_at,
         row_number() OVER (
           PARTITION BY payload->>'order_id' ORDER BY loaded_at DESC
         ) AS rn
  FROM raw.ticketing_orders
)
SELECT
  payload->>'order_id'                       AS order_id,
  payload->>'match_id'                       AS match_id,
  (payload->>'purchased_at')::timestamptz    AS purchased_at,
  payload->>'channel'                        AS channel,
  payload->>'section'                        AS section,
  (payload->>'qty')::int                     AS qty,
  (payload->>'unit_price')::numeric(10,2)    AS unit_price,
  (payload->>'total')::numeric(10,2)         AS total,
  CASE WHEN payload->>'purchaser_name' LIKE '%,%'
       THEN initcap(btrim(split_part(payload->>'purchaser_name', ',', 2)))
       ELSE initcap(split_part(btrim(payload->>'purchaser_name'), ' ', 1))
  END                                        AS first_name,
  CASE WHEN payload->>'purchaser_name' LIKE '%,%'
       THEN initcap(btrim(split_part(payload->>'purchaser_name', ',', 1)))
       ELSE initcap(regexp_replace(btrim(payload->>'purchaser_name'), '^.*\s', ''))
  END                                        AS last_name,
  lower(btrim(payload->>'purchaser_email'))  AS email,
  right(regexp_replace(coalesce(payload->>'purchaser_phone', ''), '[^0-9]', '', 'g'), 10)
                                             AS phone,
  left(nullif(payload->>'purchaser_zip', ''), 5) AS zip
FROM ranked
WHERE rn = 1;
