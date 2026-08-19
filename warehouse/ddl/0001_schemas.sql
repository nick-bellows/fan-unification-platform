-- Warehouse layout. Mirrors the Redshift deployment documented in
-- docs/redshift-migration.md; schema names are identical there.
CREATE SCHEMA IF NOT EXISTS raw;      -- landed payloads, as extracted
CREATE SCHEMA IF NOT EXISTS staging;  -- typed, normalized, deduped-within-source
CREATE SCHEMA IF NOT EXISTS identity; -- match candidates, scores, xref
CREATE SCHEMA IF NOT EXISTS core;     -- star schema (dims + facts)
CREATE SCHEMA IF NOT EXISTS marts;    -- BI-facing rollups
CREATE SCHEMA IF NOT EXISTS ops;      -- run/load audit, watermarks, dq results
