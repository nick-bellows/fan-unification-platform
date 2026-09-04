-- Anatomy of a false merge: the largest cluster the ground truth says is
-- WRONG (its members belong to more than one generated person). Shown on the
-- tour deliberately — shared household emails are the measured dominant
-- false-positive mode, and hiding the failure would contradict the repo's
-- own evaluation. Only the truth-derived COUNT is published, not per-record
-- entity assignments.
WITH worst AS (
  SELECT ct.fan_id, ct.member_count, ct.true_entity_count
  FROM ops.linkage_cluster_truth ct
  WHERE NOT ct.is_pure
  ORDER BY ct.true_entity_count DESC, ct.member_count DESC, ct.fan_id
  LIMIT 1
)
SELECT
  r.source_system,
  r.source_record_id,
  concat_ws(' ', r.first_name, r.last_name) AS observed_name,
  r.email AS observed_email,
  x.method AS cluster_method,
  w.member_count,
  w.true_entity_count
FROM staging.identity_records r
JOIN identity.fan_xref x
  ON x.source_system = r.source_system
 AND x.source_record_id = r.source_record_id
JOIN worst w ON w.fan_id = x.fan_id
ORDER BY r.email NULLS LAST, r.source_system, r.source_record_id
