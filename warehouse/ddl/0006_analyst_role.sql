-- The read-only analyst role. Table/column grants live in
-- warehouse/grants.sql and are applied by the transform flow after the marts
-- exist (they cannot run at init time on a fresh database, and marts rebuilds
-- drop them anyway).

DO $$ BEGIN
  CREATE ROLE analyst NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

GRANT USAGE ON SCHEMA marts, ops TO analyst;
