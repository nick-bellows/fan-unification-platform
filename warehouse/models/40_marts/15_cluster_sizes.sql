DROP TABLE IF EXISTS marts.cluster_sizes;
CREATE TABLE marts.cluster_sizes AS
SELECT record_count AS cluster_size, count(*) AS fans
FROM identity.golden_fans
GROUP BY record_count
ORDER BY record_count;
