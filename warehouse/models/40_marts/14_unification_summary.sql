DROP TABLE IF EXISTS marts.unification_summary;
CREATE TABLE marts.unification_summary AS
SELECT
  (SELECT count(*) FROM identity.fan_xref)                        AS source_records,
  (SELECT count(*) FROM identity.golden_fans)                     AS unified_fans,
  round((SELECT count(*) FROM identity.fan_xref)::numeric
    / nullif((SELECT count(*) FROM identity.golden_fans), 0), 2)  AS records_per_fan,
  (SELECT max(record_count) FROM identity.golden_fans)            AS largest_cluster,
  (SELECT count(*) FROM identity.golden_fans WHERE sources LIKE '%,%')
                                                                  AS multi_source_fans,
  (SELECT count(*) FROM identity.fan_xref WHERE method = 'deterministic')
                                                                  AS deterministic_records,
  (SELECT count(*) FROM identity.fan_xref WHERE method = 'probabilistic')
                                                                  AS probabilistic_records,
  (SELECT count(*) FROM identity.fan_xref WHERE method = 'singleton')
                                                                  AS singleton_records;
