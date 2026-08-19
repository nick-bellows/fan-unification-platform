-- The cross-sell question unification exists to answer: of fans whose first
-- ticket purchase fell in a month, how many bought merch within 90 days?
-- Impossible to compute without cross-system identity.
DROP TABLE IF EXISTS marts.ticket_to_merch_crossover;
CREATE TABLE marts.ticket_to_merch_crossover AS
WITH first_ticket AS (
  SELECT fan_key, min(purchased_at) AS first_ticket_at
  FROM core.fact_ticket_sales GROUP BY fan_key
),
conversion AS (
  SELECT
    f.fan_key,
    date_trunc('month', f.first_ticket_at)::date AS cohort_month,
    EXISTS (
      SELECT 1 FROM core.fact_merch_sales ms
      WHERE ms.fan_key = f.fan_key
        AND ms.created_at >= f.first_ticket_at
        AND ms.created_at < f.first_ticket_at + interval '90 days'
    ) AS converted
  FROM first_ticket f
)
SELECT
  cohort_month,
  count(*) AS new_ticket_fans,
  sum(CASE WHEN converted THEN 1 ELSE 0 END) AS bought_merch_within_90d,
  round(100.0 * sum(CASE WHEN converted THEN 1 ELSE 0 END) / count(*), 1) AS conversion_pct
FROM conversion
GROUP BY cohort_month
ORDER BY cohort_month;
