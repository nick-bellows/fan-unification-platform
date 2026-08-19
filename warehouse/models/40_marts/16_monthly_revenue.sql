DROP TABLE IF EXISTS marts.monthly_revenue;
CREATE TABLE marts.monthly_revenue AS
SELECT month, pillar, sum(revenue) AS revenue
FROM (
  SELECT date_trunc('month', purchased_at)::date AS month, 'Tickets' AS pillar,
         total AS revenue
  FROM core.fact_ticket_sales
  UNION ALL
  SELECT date_trunc('month', created_at)::date, 'Merch', line_total
  FROM core.fact_merch_sales
  UNION ALL
  SELECT date_trunc('month', close_date)::date,
         CASE WHEN type = 'Membership' THEN 'Memberships' ELSE 'Donations' END,
         amount
  FROM core.fact_giving
) unioned
GROUP BY month, pillar
ORDER BY month, pillar;
