-- One row per unified fan: identity plus rolled-up activity across every
-- pillar. CASE-based conditional sums (not FILTER) for Redshift portability.
DROP TABLE IF EXISTS marts.fan_360;
CREATE TABLE marts.fan_360 AS
WITH tickets AS (
  SELECT fan_key, count(*) AS ticket_orders, sum(qty) AS seats,
         sum(total) AS ticket_revenue, max(purchased_at) AS last_ticket_at
  FROM core.fact_ticket_sales GROUP BY fan_key
),
merch AS (
  SELECT fan_key, count(DISTINCT order_number) AS merch_orders,
         sum(line_total) AS merch_revenue, max(created_at) AS last_merch_at
  FROM core.fact_merch_sales GROUP BY fan_key
),
giving AS (
  SELECT fan_key,
         sum(CASE WHEN type = 'Membership' THEN amount ELSE 0 END) AS membership_revenue,
         sum(CASE WHEN type = 'Donation'  THEN amount ELSE 0 END) AS donation_revenue,
         max(close_date) AS last_gift_on
  FROM core.fact_giving GROUP BY fan_key
),
email AS (
  SELECT fan_key,
         sum(CASE WHEN event_type = 'send'  THEN 1 ELSE 0 END) AS sends,
         sum(CASE WHEN event_type = 'open'  THEN 1 ELSE 0 END) AS opens,
         sum(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) AS clicks
  FROM core.fact_email_engagement GROUP BY fan_key
)
SELECT
  f.fan_key, f.fan_id, f.first_name, f.last_name, f.email,
  f.city, f.state, f.zip, f.sources, f.record_count,
  coalesce(t.ticket_orders, 0)      AS ticket_orders,
  coalesce(t.seats, 0)              AS seats,
  coalesce(t.ticket_revenue, 0)     AS ticket_revenue,
  coalesce(m.merch_orders, 0)       AS merch_orders,
  coalesce(m.merch_revenue, 0)      AS merch_revenue,
  coalesce(g.membership_revenue, 0) AS membership_revenue,
  coalesce(g.donation_revenue, 0)   AS donation_revenue,
  coalesce(t.ticket_revenue, 0) + coalesce(m.merch_revenue, 0)
    + coalesce(g.membership_revenue, 0) + coalesce(g.donation_revenue, 0)
                                    AS total_revenue,
  coalesce(e.sends, 0)              AS email_sends,
  coalesce(e.opens, 0)              AS email_opens,
  coalesce(e.clicks, 0)             AS email_clicks,
  CASE WHEN coalesce(e.sends, 0) > 0
       THEN round(100.0 * e.opens / e.sends, 1) ELSE NULL END AS open_rate_pct,
  greatest(t.last_ticket_at, m.last_merch_at)::date AS last_purchase_on
FROM core.dim_fan f
LEFT JOIN tickets t ON t.fan_key = f.fan_key
LEFT JOIN merch m ON m.fan_key = f.fan_key
LEFT JOIN giving g ON g.fan_key = f.fan_key
LEFT JOIN email e ON e.fan_key = f.fan_key
WHERE f.is_current;
