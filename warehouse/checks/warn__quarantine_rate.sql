-- More than 1% of a source's landed rows in quarantine deserves attention.
WITH landed AS (
  SELECT 'crm_contacts' AS source, count(*) AS n FROM raw.crm_contacts
  UNION ALL SELECT 'ticketing_orders', count(*) FROM raw.ticketing_orders
  UNION ALL SELECT 'merch_order_items', count(*) FROM raw.merch_order_items
  UNION ALL SELECT 'email_subscribers', count(*) FROM raw.email_subscribers
  UNION ALL SELECT 'email_events', count(*) FROM raw.email_events
),
quarantined AS (
  SELECT source, count(*) AS n FROM raw.quarantine GROUP BY source
)
SELECT l.source, q.n AS quarantined, l.n AS landed
FROM landed l
JOIN quarantined q ON q.source = l.source
WHERE q.n > 0.01 * (l.n + q.n)
