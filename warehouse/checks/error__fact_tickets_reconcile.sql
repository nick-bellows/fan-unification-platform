-- Row-count and revenue totals must survive the staging -> fact join exactly.
SELECT 'count' AS measure, s.n::text AS staging_value, f.n::text AS fact_value
FROM (SELECT count(*) AS n FROM staging.stg_ticketing_orders) s,
     (SELECT count(*) AS n FROM core.fact_ticket_sales) f
WHERE s.n <> f.n
UNION ALL
SELECT 'revenue', s.v::text, f.v::text
FROM (SELECT coalesce(sum(total), 0) AS v FROM staging.stg_ticketing_orders) s,
     (SELECT coalesce(sum(total), 0) AS v FROM core.fact_ticket_sales) f
WHERE s.v <> f.v
