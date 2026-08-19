-- The upstream export renamed billing_zip -> billing_postal_code mid-history
-- and added discount_code (schema drift); coalesce folds both generations into
-- one column so downstream models never see the drift.
DROP TABLE IF EXISTS staging.stg_merch_order_items;
CREATE TABLE staging.stg_merch_order_items AS
SELECT
  payload->>'order_number'                   AS order_number,
  (payload->>'created_at')::timestamptz      AS created_at,
  lower(btrim(payload->>'customer_email'))   AS email,
  initcap(split_part(btrim(payload->>'billing_name'), ' ', 1)) AS first_name,
  initcap(regexp_replace(btrim(payload->>'billing_name'), '^.*\s', '')) AS last_name,
  left(nullif(coalesce(payload->>'billing_zip', payload->>'billing_postal_code'), ''), 5)
                                             AS zip,
  nullif(payload->>'discount_code', '')      AS discount_code,
  payload->>'sku'                            AS sku,
  payload->>'item_name'                      AS item_name,
  (payload->>'quantity')::int                AS quantity,
  (payload->>'unit_price')::numeric(10,2)    AS unit_price,
  (payload->>'line_total')::numeric(10,2)    AS line_total
FROM raw.merch_order_items;
