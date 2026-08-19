# ADR 0002: Postgres-as-Redshift, MinIO-as-S3

**Status:** accepted · **Date:** 2026-08-19

## Context

The target role manages a warehouse in AWS Redshift. Redshift Serverless bills
per RPU-hour with an 8-RPU floor; leaving it running for a portfolio project
costs real money for no reader benefit. The project must cost $0 and be
reproducible from a clean clone with `docker compose up`.

## Decision

- **Postgres 16** is the warehouse. Redshift derives from Postgres, so the SQL
  dialect, the schema/permission model, and the COPY-based load pattern carry
  over; the divergences that matter (DISTKEY/SORTKEY, unenforced constraints,
  COPY-from-S3 syntax, VACUUM/ANALYZE) are documented in
  `docs/redshift-migration.md` with Redshift DDL variants in
  `warehouse/redshift/`.
- **MinIO** provides the lake. It speaks the real S3 API, so all object-store
  code uses genuine `boto3` with an `endpoint_url` override — pointing the same
  code at AWS S3 is a one-variable change.
- `infra/terraform/` defines the real deployment (S3 bucket, Redshift
  Serverless namespace/workgroup, COPY IAM role) and is validated in CI, never
  applied.

## Consequences

- Zero hosting cost; the whole stack runs locally and in CI.
- Load code exercises the honest pattern (object store + COPY), not a
  local-file shortcut.
- Redshift-specific performance behavior (distribution, columnar encodings)
  cannot be demonstrated live — only documented. Accepted trade-off.
