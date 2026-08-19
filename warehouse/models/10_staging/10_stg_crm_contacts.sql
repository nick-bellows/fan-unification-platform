-- Latest version per contact: raw is an append-only extraction log, so a
-- contact re-extracted after an update appears twice; the newest
-- SystemModstamp wins (loaded_at breaks ties).
DROP TABLE IF EXISTS staging.stg_crm_contacts;
CREATE TABLE staging.stg_crm_contacts AS
WITH ranked AS (
  SELECT payload, loaded_at,
         row_number() OVER (
           PARTITION BY payload->>'Id'
           ORDER BY payload->>'SystemModstamp' DESC, loaded_at DESC
         ) AS rn
  FROM raw.crm_contacts
)
SELECT
  payload->>'Id'                                         AS contact_id,
  initcap(btrim(payload->>'FirstName'))                  AS first_name,
  initcap(btrim(payload->>'LastName'))                   AS last_name,
  lower(btrim(payload->>'Email'))                        AS email,
  right(regexp_replace(coalesce(payload->>'Phone', ''), '[^0-9]', '', 'g'), 10) AS phone,
  payload->>'MailingCity'                                AS city,
  payload->>'MailingState'                               AS state,
  left(payload->>'MailingPostalCode', 5)                 AS zip,
  (payload->>'Birthdate')::date                          AS dob,
  (payload->>'Member_Since__c')::date                    AS member_since,
  (payload->>'SystemModstamp')::timestamptz              AS modified_at
FROM ranked
WHERE rn = 1;
