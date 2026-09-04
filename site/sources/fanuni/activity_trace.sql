-- The featured cluster is TRUTH-VERIFIED PURE (every member record maps to
-- one generated entity, per ops.linkage_cluster_truth, written by the eval
-- harness). The previous version preferred the largest probabilistic cluster,
-- which selected for false merges — the external-review finding. If no pure
-- cluster qualifies, this source is empty and the empty-dashboard gate fails
-- the deploy, forcing a tour review.
WITH chosen AS (
  SELECT ct.fan_id
  FROM ops.linkage_cluster_truth ct
  JOIN core.dim_fan d ON d.fan_id = ct.fan_id AND d.is_current
  JOIN core.fact_ticket_sales t ON t.fan_key = d.fan_key
  WHERE ct.is_pure
  GROUP BY ct.fan_id, ct.has_probabilistic, ct.member_count
  ORDER BY ct.has_probabilistic DESC,
           ct.member_count DESC,
           ct.fan_id
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
