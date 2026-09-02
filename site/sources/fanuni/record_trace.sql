WITH chosen AS (
  SELECT x.fan_id
  FROM identity.fan_xref x
  JOIN core.dim_fan d ON d.fan_id = x.fan_id AND d.is_current
  JOIN core.fact_ticket_sales t ON t.fan_key = d.fan_key
  GROUP BY x.fan_id
  ORDER BY bool_or(x.method = 'probabilistic') DESC,
           max(d.record_count) DESC,
           x.fan_id
  LIMIT 1
)
SELECT
  r.source_system,
  r.source_record_id,
  concat_ws(' ', r.first_name, r.last_name) AS observed_name,
  r.email AS observed_email,
  r.phone AS observed_phone,
  r.zip AS observed_zip,
  x.method AS cluster_method,
  x.score AS probabilistic_score,
  CASE
    WHEN x.method = 'probabilistic'
      THEN 'probabilistic score met the auto-merge threshold'
    WHEN x.method = 'deterministic' AND EXISTS (
      SELECT 1
      FROM staging.identity_records other
      JOIN identity.fan_xref other_x
        ON other_x.source_system = other.source_system
       AND other_x.source_record_id = other.source_record_id
      WHERE other_x.fan_id = x.fan_id
        AND (other.source_system, other.source_record_id)
            <> (r.source_system, r.source_record_id)
        AND r.email IS NOT NULL
        AND lower(trim(other.email)) = lower(trim(r.email))
    ) THEN 'exact normalized email evidence'
    WHEN x.method = 'deterministic' AND EXISTS (
      SELECT 1
      FROM staging.identity_records other
      JOIN identity.fan_xref other_x
        ON other_x.source_system = other.source_system
       AND other_x.source_record_id = other.source_record_id
      WHERE other_x.fan_id = x.fan_id
        AND (other.source_system, other.source_record_id)
            <> (r.source_system, r.source_record_id)
        AND r.phone IS NOT NULL
        AND other.phone = r.phone
        AND lower(trim(other.last_name)) = lower(trim(r.last_name))
    ) THEN 'exact phone and surname evidence'
    WHEN x.method = 'deterministic'
      THEN 'connected through a deterministic cluster edge'
    ELSE 'no linked record; retained as a singleton'
  END AS match_evidence,
  x.fan_id
FROM staging.identity_records r
JOIN identity.fan_xref x
  ON x.source_system = r.source_system
 AND x.source_record_id = r.source_record_id
JOIN chosen c ON c.fan_id = x.fan_id
ORDER BY r.source_system, r.source_record_id
