-- Line-item grain so product analysis works.
DROP TABLE IF EXISTS core.fact_merch_sales;
CREATE TABLE core.fact_merch_sales AS
SELECT
  i.order_number,
  f.fan_key,
  p.product_key,
  to_char(i.created_at, 'YYYYMMDD')::int AS date_key,
  i.created_at,
  i.quantity,
  i.unit_price,
  i.line_total,
  i.discount_code
FROM staging.stg_merch_order_items i
JOIN identity.fan_xref x
  ON x.source_system = 'merch' AND x.source_record_id = i.order_number
JOIN core.dim_fan f ON f.fan_id = x.fan_id AND f.is_current
JOIN core.dim_product p ON p.sku = i.sku;
