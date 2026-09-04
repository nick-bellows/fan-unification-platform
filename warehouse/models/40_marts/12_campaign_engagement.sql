DROP TABLE IF EXISTS marts.campaign_engagement;
CREATE TABLE marts.campaign_engagement AS
SELECT
  c.campaign_key, c.campaign_id, c.name, c.sent_date,
  sum(CASE WHEN e.event_type = 'send'  THEN 1 ELSE 0 END) AS sends,
  sum(CASE WHEN e.event_type = 'open'  THEN 1 ELSE 0 END) AS opens,
  sum(CASE WHEN e.event_type = 'click' THEN 1 ELSE 0 END) AS clicks,
  round(100.0 * sum(CASE WHEN e.event_type = 'open' THEN 1 ELSE 0 END)
    / nullif(sum(CASE WHEN e.event_type = 'send' THEN 1 ELSE 0 END), 0), 1) AS open_rate_pct,
  round(100.0 * sum(CASE WHEN e.event_type = 'click' THEN 1 ELSE 0 END)
    / nullif(sum(CASE WHEN e.event_type = 'send' THEN 1 ELSE 0 END), 0), 1) AS click_rate_pct
FROM core.dim_campaign c
LEFT JOIN core.fact_email_engagement e ON e.campaign_id = c.campaign_id
GROUP BY c.campaign_key, c.campaign_id, c.name, c.sent_date;
