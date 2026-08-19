-- Latest evaluation only: per-variant, per-tag recall
SELECT t.*
FROM ops.linkage_eval_tags t
WHERE t.evaluated_at = (SELECT max(evaluated_at) FROM ops.linkage_eval_tags)
ORDER BY t.variant, t.tag
