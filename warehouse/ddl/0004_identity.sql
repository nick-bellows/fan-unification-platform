-- The unification interface. The unifier (deterministic from M3, +Splink from
-- M4) fully rebuilds these two tables each run; the SQL model layer only ever
-- reads them. fan_ids derive from the minimum member record of a cluster, so
-- they are stable across runs for stable clusters — which is what makes SCD2
-- history on core.dim_fan meaningful.

CREATE TABLE IF NOT EXISTS identity.fan_xref (
  source_system    text NOT NULL,
  source_record_id text NOT NULL,
  fan_id           text NOT NULL,
  method           text NOT NULL,   -- deterministic | probabilistic | singleton
  score            real,            -- match probability where probabilistic
  PRIMARY KEY (source_system, source_record_id)
);

CREATE INDEX IF NOT EXISTS fan_xref_fan_id ON identity.fan_xref (fan_id);

CREATE TABLE IF NOT EXISTS identity.golden_fans (
  fan_id       text PRIMARY KEY,
  first_name   text,
  last_name    text,
  email        text,
  phone        text,
  city         text,
  state        text,
  zip          text,
  dob          date,
  sources      text NOT NULL,      -- comma-joined, e.g. 'crm,email,ticketing'
  record_count integer NOT NULL
);
