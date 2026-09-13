-- Staging identity keys must be unique after within-source dedupe.
SELECT 'stg_crm_contacts' AS tbl, contact_id AS id, count(*)
FROM staging.stg_crm_contacts GROUP BY contact_id HAVING count(*) > 1
UNION ALL
SELECT 'stg_ticketing_orders', order_id, count(*)
FROM staging.stg_ticketing_orders GROUP BY order_id HAVING count(*) > 1
UNION ALL
SELECT 'stg_email_subscribers', subscriber_id, count(*)
FROM staging.stg_email_subscribers GROUP BY subscriber_id HAVING count(*) > 1
-- stg_merch_orders is GROUP BY order_number by construction, so a uniqueness
-- check on it could never fail; merch is covered by its fact reconcile.
