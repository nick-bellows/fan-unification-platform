-- Order-grain rollup of the line items; the per-order purchaser identity is
-- what feeds identity_records.
DROP TABLE IF EXISTS staging.stg_merch_orders;
CREATE TABLE staging.stg_merch_orders AS
SELECT
  order_number,
  min(created_at)  AS created_at,
  min(email)       AS email,
  min(first_name)  AS first_name,
  min(last_name)   AS last_name,
  min(zip)         AS zip,
  sum(quantity)    AS items,
  sum(line_total)  AS order_total
FROM staging.stg_merch_order_items
GROUP BY order_number;
