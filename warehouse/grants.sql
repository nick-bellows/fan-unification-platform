-- Warehouse data security: the analyst role reads marts but never raw PII.
-- Column-level grants (also supported in Redshift) expose fan_360 minus the
-- identifying columns; identity/raw/staging schemas are not granted at all.
-- Applied by the transform flow after every marts rebuild (which drops
-- grants); the role itself is created in ddl/0006_analyst_role.sql.

GRANT SELECT ON
  marts.revenue_by_match,
  marts.monthly_revenue,
  marts.campaign_engagement,
  marts.ticket_to_merch_crossover,
  marts.unification_summary,
  marts.cluster_sizes
TO analyst;

-- fan_360 minus PII (no name, email, city, zip; state stays — coarse
-- geography, consistent with the data dictionary's classification).
GRANT SELECT (
  fan_key, fan_id, state, sources, record_count,
  ticket_orders, seats, ticket_revenue,
  merch_orders, merch_revenue,
  membership_revenue, donation_revenue, total_revenue,
  email_sends, email_opens, email_clicks, open_rate_pct, last_purchase_on
) ON marts.fan_360 TO analyst;

GRANT SELECT ON ops.dq_results, ops.pipeline_runs, ops.model_runs TO analyst;
