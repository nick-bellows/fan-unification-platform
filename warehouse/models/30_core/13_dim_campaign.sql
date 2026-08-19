DROP TABLE IF EXISTS core.dim_campaign;
CREATE TABLE core.dim_campaign AS
SELECT
  row_number() OVER (ORDER BY campaign_id)::int AS campaign_key,
  campaign_id,
  name,
  sent_at,
  sent_at::date AS sent_date
FROM staging.stg_email_campaigns;
