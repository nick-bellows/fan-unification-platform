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
