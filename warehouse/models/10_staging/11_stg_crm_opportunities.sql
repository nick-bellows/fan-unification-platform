DROP TABLE IF EXISTS staging.stg_crm_opportunities;
CREATE TABLE staging.stg_crm_opportunities AS
WITH ranked AS (
  SELECT payload, loaded_at,
         row_number() OVER (
           PARTITION BY payload->>'Id'
           ORDER BY payload->>'SystemModstamp' DESC, loaded_at DESC
         ) AS rn
  FROM raw.crm_opportunities
)
SELECT
  payload->>'Id'                             AS opportunity_id,
  payload->>'ContactId'                      AS contact_id,
  payload->>'Type'                           AS type,
  (payload->>'Amount')::numeric(10,2)        AS amount,
  (payload->>'CloseDate')::date              AS close_date,
  (payload->>'SystemModstamp')::timestamptz  AS modified_at
FROM ranked
WHERE rn = 1;
