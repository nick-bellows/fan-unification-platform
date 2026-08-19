-- Redshift DDL variants for the core schema (see docs/redshift-migration.md).
-- Differences from the Postgres models: explicit DISTKEY/SORTKEY replace
-- indexes; IDENTITY syntax differs; constraints are informational only.

CREATE TABLE core.dim_fan (
  fan_key      bigint IDENTITY(1, 1),
  fan_id       varchar(24) NOT NULL,
  first_name   varchar(64),
  last_name    varchar(64),
  email        varchar(256),
  phone        varchar(16),
  city         varchar(64),
  state        varchar(2),
  zip          varchar(5),
  dob          date,
  sources      varchar(64),
  record_count integer,
  valid_from   timestamptz NOT NULL DEFAULT sysdate,
  valid_to     timestamptz,
  is_current   boolean NOT NULL DEFAULT true,
  PRIMARY KEY (fan_key) -- informational in Redshift; ops checks enforce it
)
DISTKEY (fan_id)   -- co-locate a fan's versions and their fact joins
SORTKEY (fan_id, is_current);

CREATE TABLE core.fact_ticket_sales (
  order_id     varchar(16) NOT NULL,
  fan_key      bigint NOT NULL,
  match_key    integer,
  date_key     integer NOT NULL,
  purchased_at timestamptz NOT NULL,
  channel      varchar(16),
  section      varchar(16),
  qty          smallint NOT NULL,
  unit_price   decimal(10, 2),
  total        decimal(10, 2)
)
DISTKEY (fan_key)  -- the dominant join is fact -> dim_fan
SORTKEY (date_key);

CREATE TABLE core.fact_email_engagement (
  event_id     varchar(16) NOT NULL,
  fan_key      bigint NOT NULL,
  campaign_key integer NOT NULL,
  date_key     integer NOT NULL,
  event_type   varchar(8) NOT NULL,
  occurred_at  timestamptz NOT NULL
)
DISTKEY (fan_key)
SORTKEY (date_key, campaign_key);

-- Small dimensions distribute everywhere so joins never shuffle them.
-- dim_date / dim_match / dim_product / dim_campaign: DISTSTYLE ALL,
-- SORTKEY on their natural key, e.g.:
--   CREATE TABLE core.dim_match (...) DISTSTYLE ALL SORTKEY (match_key);
