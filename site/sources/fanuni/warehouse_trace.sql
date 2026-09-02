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
  d.fan_id,
  d.fan_key,
  concat_ws(' ', d.first_name, d.last_name) AS canonical_name,
  d.email AS canonical_email,
  d.sources,
  d.record_count,
  d.valid_from,
  d.valid_to,
  d.is_current,
  f.ticket_orders,
  f.ticket_revenue,
  f.merch_orders,
  f.merch_revenue,
  f.email_sends,
  f.email_opens,
  f.total_revenue
FROM core.dim_fan d
JOIN chosen c ON c.fan_id = d.fan_id
LEFT JOIN marts.fan_360 f ON f.fan_key = d.fan_key
ORDER BY d.valid_from
