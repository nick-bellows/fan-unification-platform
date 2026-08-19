-- The golden-record dimension, maintained as a hybrid SCD:
--   type 2 (versioned) for identity attributes: name, email, phone, zip, dob,
--     city/state — a change closes the current version and opens a new one;
--   type 1 (updated in place) for activity attributes: sources, record_count —
--     these grow on nearly every load and would churn versions meaninglessly.
-- This model is incremental on purpose: the table persists across runs so the
-- version history is real. Rebuild = DROP TABLE core.dim_fan, then rerun.

CREATE TABLE IF NOT EXISTS core.dim_fan (
  fan_key      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  fan_id       text NOT NULL,
  first_name   text,
  last_name    text,
  email        text,
  phone        text,
  city         text,
  state        text,
  zip          text,
  dob          date,
  sources      text,
  record_count integer,
  valid_from   timestamptz NOT NULL DEFAULT now(),
  valid_to     timestamptz,
  is_current   boolean NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS dim_fan_fan_id_current ON core.dim_fan (fan_id) WHERE is_current;

-- 1. Close current versions whose type-2 attributes changed.
UPDATE core.dim_fan d
SET valid_to = now(), is_current = false
FROM identity.golden_fans g
WHERE d.is_current AND d.fan_id = g.fan_id
  AND (d.first_name IS DISTINCT FROM g.first_name
    OR d.last_name  IS DISTINCT FROM g.last_name
    OR d.email      IS DISTINCT FROM g.email
    OR d.phone      IS DISTINCT FROM g.phone
    OR d.city       IS DISTINCT FROM g.city
    OR d.state      IS DISTINCT FROM g.state
    OR d.zip        IS DISTINCT FROM g.zip
    OR d.dob        IS DISTINCT FROM g.dob);

-- 2. Retire versions whose fan_id left the golden set (cluster re-shaped).
UPDATE core.dim_fan d
SET valid_to = now(), is_current = false
WHERE d.is_current
  AND NOT EXISTS (SELECT 1 FROM identity.golden_fans g WHERE g.fan_id = d.fan_id);

-- 3. Open versions for new or changed fans.
INSERT INTO core.dim_fan
  (fan_id, first_name, last_name, email, phone, city, state, zip, dob,
   sources, record_count)
SELECT g.fan_id, g.first_name, g.last_name, g.email, g.phone, g.city, g.state,
       g.zip, g.dob, g.sources, g.record_count
FROM identity.golden_fans g
WHERE NOT EXISTS (
  SELECT 1 FROM core.dim_fan d WHERE d.fan_id = g.fan_id AND d.is_current
);

-- 4. Type-1 refresh of activity attributes on current versions.
UPDATE core.dim_fan d
SET sources = g.sources, record_count = g.record_count
FROM identity.golden_fans g
WHERE d.is_current AND d.fan_id = g.fan_id
  AND (d.sources IS DISTINCT FROM g.sources
    OR d.record_count IS DISTINCT FROM g.record_count);
