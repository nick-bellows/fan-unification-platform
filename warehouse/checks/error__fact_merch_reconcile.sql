-- Line count and revenue must survive the staging -> fact join exactly; a
-- gap means the xref or product join dropped merch lines silently.
SELECT 'count' AS measure, s.n::text AS staging_value, f.n::text AS fact_value
FROM (SELECT count(*) AS n FROM staging.stg_merch_order_items) s,
     (SELECT count(*) AS n FROM core.fact_merch_sales) f
WHERE s.n <> f.n
UNION ALL
SELECT 'revenue', s.v::text, f.v::text
FROM (SELECT coalesce(sum(line_total), 0) AS v FROM staging.stg_merch_order_items) s,
     (SELECT coalesce(sum(line_total), 0) AS v FROM core.fact_merch_sales) f
WHERE s.v <> f.v
