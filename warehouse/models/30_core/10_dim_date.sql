-- Spans the observed activity window with a small buffer. In Redshift,
-- generate_series cannot feed a CTAS (leader-node-only function); the
-- migration doc swaps this for a numbers-table build.
DROP TABLE IF EXISTS core.dim_date;
CREATE TABLE core.dim_date AS
WITH bounds AS (
  SELECT
    least(
      (SELECT min(purchased_at)::date FROM staging.stg_ticketing_orders),
      (SELECT min(created_at)::date   FROM staging.stg_merch_orders),
      (SELECT min(occurred_at)::date  FROM staging.stg_email_events),
      (SELECT min(kickoff_at)::date   FROM staging.stg_fixtures),
      (SELECT min(close_date)         FROM staging.stg_crm_opportunities)
    ) - 7 AS lo,
    greatest(
      (SELECT max(purchased_at)::date FROM staging.stg_ticketing_orders),
      (SELECT max(created_at)::date   FROM staging.stg_merch_orders),
      (SELECT max(occurred_at)::date  FROM staging.stg_email_events),
      (SELECT max(kickoff_at)::date   FROM staging.stg_fixtures),
      (SELECT max(close_date)         FROM staging.stg_crm_opportunities)
    ) + 7 AS hi
)
SELECT
  to_char(d, 'YYYYMMDD')::int   AS date_key,
  d::date                       AS date,
  extract(year FROM d)::int     AS year,
  extract(quarter FROM d)::int  AS quarter,
  extract(month FROM d)::int    AS month,
  to_char(d, 'Mon')             AS month_name,
  extract(day FROM d)::int      AS day,
  extract(isodow FROM d)::int   AS iso_dow,
  extract(isodow FROM d) >= 6   AS is_weekend
FROM bounds, generate_series(lo::timestamp, hi::timestamp, interval '1 day') AS d;
