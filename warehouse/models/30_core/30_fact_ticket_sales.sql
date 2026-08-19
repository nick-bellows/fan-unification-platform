DROP TABLE IF EXISTS core.fact_ticket_sales;
CREATE TABLE core.fact_ticket_sales AS
SELECT
  o.order_id,
  f.fan_key,
  m.match_key,
  to_char(o.purchased_at, 'YYYYMMDD')::int AS date_key,
  o.purchased_at,
  o.channel,
  o.section,
  o.qty,
  o.unit_price,
  o.total
FROM staging.stg_ticketing_orders o
JOIN identity.fan_xref x
  ON x.source_system = 'ticketing' AND x.source_record_id = o.order_id
JOIN core.dim_fan f ON f.fan_id = x.fan_id AND f.is_current
LEFT JOIN core.dim_match m ON m.match_id = o.match_id;
