DROP TABLE IF EXISTS staging.stg_fixtures;
CREATE TABLE staging.stg_fixtures AS
SELECT
  payload->>'match_id'                       AS match_id,
  (payload->>'kickoff_at')::timestamptz      AS kickoff_at,
  payload->>'home_team'                      AS home_team,
  payload->>'away_team'                      AS away_team,
  payload->>'venue'                          AS venue,
  payload->>'city'                           AS city,
  payload->>'competition'                    AS competition
FROM raw.fixtures;
