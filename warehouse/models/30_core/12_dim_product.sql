DROP TABLE IF EXISTS core.dim_product;
CREATE TABLE core.dim_product AS
SELECT
  row_number() OVER (ORDER BY sku)::int AS product_key,
  sku,
  max(item_name)  AS item_name,
  max(unit_price) AS list_price,
  CASE
    WHEN sku LIKE 'JER-%'  THEN 'Jerseys'
    WHEN sku LIKE 'KIT-%'  THEN 'Kits'
    WHEN sku IN ('SCARF-CL', 'CAP-CL', 'HOOD-CR') THEN 'Apparel'
    WHEN sku = 'BALL-RP'   THEN 'Equipment'
    ELSE 'Accessories'
  END AS category
FROM staging.stg_merch_order_items
GROUP BY sku;
