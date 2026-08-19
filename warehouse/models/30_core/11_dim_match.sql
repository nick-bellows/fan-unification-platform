DROP TABLE IF EXISTS core.dim_match;
CREATE TABLE core.dim_match AS
SELECT
  row_number() OVER (ORDER BY match_id)::int AS match_key,
  match_id,
  kickoff_at,
  kickoff_at::date AS match_date,
  home_team,
  away_team,
  venue,
  city,
  competition
FROM staging.stg_fixtures;
