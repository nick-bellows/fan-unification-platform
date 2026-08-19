-- Memberships and donations from the CRM, at opportunity grain.
DROP TABLE IF EXISTS core.fact_giving;
CREATE TABLE core.fact_giving AS
SELECT
  o.opportunity_id,
  f.fan_key,
  o.type,
  o.amount,
  to_char(o.close_date, 'YYYYMMDD')::int AS date_key,
  o.close_date
FROM staging.stg_crm_opportunities o
JOIN identity.fan_xref x
  ON x.source_system = 'crm' AND x.source_record_id = o.contact_id
JOIN core.dim_fan f ON f.fan_id = x.fan_id AND f.is_current;
