-- Every xref target must exist in golden_fans and as a current dim_fan row.
SELECT DISTINCT x.fan_id
FROM identity.fan_xref x
LEFT JOIN identity.golden_fans g ON g.fan_id = x.fan_id
LEFT JOIN core.dim_fan d ON d.fan_id = x.fan_id AND d.is_current
WHERE g.fan_id IS NULL OR d.fan_id IS NULL
