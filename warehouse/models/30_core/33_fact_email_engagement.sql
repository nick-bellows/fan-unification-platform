-- The incremental fact (the pattern shown once, deliberately): event grain,
-- append-only by event_id. Note the trade-off: if unification later reassigns
-- a subscriber to a different fan, rows already loaded keep their original
-- fan_key. Rebuild = DROP TABLE core.fact_email_engagement, then rerun.
CREATE TABLE IF NOT EXISTS core.fact_email_engagement (
  event_id     text PRIMARY KEY,
  fan_key      bigint NOT NULL,
  campaign_key integer NOT NULL,
  date_key     integer NOT NULL,
  event_type   text NOT NULL,
  occurred_at  timestamptz NOT NULL
);

INSERT INTO core.fact_email_engagement
  (event_id, fan_key, campaign_key, date_key, event_type, occurred_at)
SELECT
  e.event_id,
  f.fan_key,
  c.campaign_key,
  to_char(e.occurred_at, 'YYYYMMDD')::int,
  e.event_type,
  e.occurred_at
FROM staging.stg_email_events e
JOIN identity.fan_xref x
  ON x.source_system = 'email' AND x.source_record_id = e.subscriber_id
JOIN core.dim_fan f ON f.fan_id = x.fan_id AND f.is_current
JOIN core.dim_campaign c ON c.campaign_id = e.campaign_id
WHERE NOT EXISTS (
  SELECT 1 FROM core.fact_email_engagement t WHERE t.event_id = e.event_id
);
