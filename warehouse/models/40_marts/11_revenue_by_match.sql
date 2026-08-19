DROP TABLE IF EXISTS marts.revenue_by_match;
CREATE TABLE marts.revenue_by_match AS
SELECT
  m.match_key, m.match_id, m.match_date, m.home_team, m.away_team,
  m.venue, m.city, m.competition,
  count(s.order_id)          AS orders,
  coalesce(sum(s.qty), 0)    AS seats_sold,
  coalesce(sum(s.total), 0)  AS ticket_revenue,
  count(DISTINCT s.fan_key)  AS unique_buyers
FROM core.dim_match m
LEFT JOIN core.fact_ticket_sales s ON s.match_key = m.match_key
GROUP BY m.match_key, m.match_id, m.match_date, m.home_team, m.away_team,
         m.venue, m.city, m.competition;
