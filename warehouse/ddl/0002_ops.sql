-- Operational audit tables. Every flow run and every load writes here; the
-- ops dashboard and the freshness checks read from here.

CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
  run_id      text PRIMARY KEY,
  flow_name   text NOT NULL,
  parameters  jsonb NOT NULL DEFAULT '{}'::jsonb,
  status      text NOT NULL DEFAULT 'running',  -- running | completed | failed
  started_at  timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS ops.load_audit (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id        text NOT NULL,
  source        text NOT NULL,
  object_key    text NOT NULL,          -- lake key the rows came from
  target_table  text NOT NULL,
  rows_loaded   integer NOT NULL,
  rows_rejected integer NOT NULL DEFAULT 0,
  loaded_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.watermarks (
  source          text PRIMARY KEY,
  watermark_value text NOT NULL,
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.ingested_files (
  source      text NOT NULL,
  file_name   text NOT NULL,
  sha256      text NOT NULL,
  object_key  text NOT NULL,
  rows        integer NOT NULL,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source, file_name)
);

CREATE TABLE IF NOT EXISTS ops.model_runs (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id      text NOT NULL,
  model       text NOT NULL,
  schema_name text NOT NULL,
  rows        bigint NOT NULL,
  duration_ms integer NOT NULL,
  executed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.dq_results (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id     text NOT NULL,
  check_name text NOT NULL,
  severity   text NOT NULL,             -- error | warn
  passed     boolean NOT NULL,
  failed_rows integer,
  detail     text,
  checked_at timestamptz NOT NULL DEFAULT now()
);
