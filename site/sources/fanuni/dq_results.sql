-- Most recent result per check
SELECT DISTINCT ON (check_name)
  check_name, severity, passed, failed_rows, detail, checked_at
FROM ops.dq_results
ORDER BY check_name, checked_at DESC
