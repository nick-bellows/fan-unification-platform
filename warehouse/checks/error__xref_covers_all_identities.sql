-- Every identity-bearing record must resolve to a fan; a gap here means
-- facts silently drop rows on their xref join.
SELECT r.source_system, r.source_record_id
FROM staging.identity_records r
LEFT JOIN identity.fan_xref x
  ON x.source_system = r.source_system
 AND x.source_record_id = r.source_record_id
WHERE x.fan_id IS NULL
