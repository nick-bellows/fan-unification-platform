WITH chosen AS (
  SELECT x.fan_id
  FROM identity.fan_xref x
  JOIN core.dim_fan d ON d.fan_id = x.fan_id AND d.is_current
  JOIN core.fact_ticket_sales t ON t.fan_key = d.fan_key
  GROUP BY x.fan_id
  ORDER BY bool_or(x.method = 'probabilistic') DESC,
           max(d.record_count) DESC,
           x.fan_id
  LIMIT 1
)
SELECT
  t.order_id,
  t.fan_key,
  m.match_id,
  m.match_date,
  m.home_team,
  m.away_team,
  t.channel,
  t.qty AS seats,
  t.total AS ticket_revenue
FROM core.fact_ticket_sales t
JOIN core.dim_fan d ON d.fan_key = t.fan_key
JOIN chosen c ON c.fan_id = d.fan_id
LEFT JOIN core.dim_match m ON m.match_key = t.match_key
ORDER BY t.purchased_at
LIMIT 10
