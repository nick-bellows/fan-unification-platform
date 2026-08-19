# Redshift migration notes

Postgres 16 stands in for Redshift locally (ADR 0002). Redshift derives from
Postgres 8.0, so most of this repo's SQL runs unchanged; this page lists every
divergence that matters, in the order the pipeline would hit them. The
Terraform for the real deployment is in `infra/terraform/`; Redshift DDL
variants for the hot tables are in `warehouse/redshift/`.

| Area | Local (Postgres 16) | Redshift |
| --- | --- | --- |
| Load path | `COPY ... FROM STDIN` over the wire from Python | `COPY table FROM 's3://bucket/key' IAM_ROLE '<arn>' FORMAT JSON 'auto'` — the lake key layout (`raw/<source>/...`) is already what that COPY wants; the loader would issue COPY-from-S3 instead of streaming rows |
| Raw payloads | `jsonb` + `->>` operators | `SUPER` + PartiQL navigation (`payload.email`); staging models change accessor syntax only |
| Indexes | B-tree + partial indexes (e.g. `dim_fan (fan_id) WHERE is_current`) | No indexes; DISTKEY/SORTKEY instead — see `warehouse/redshift/core_tables.sql` |
| Constraints | PK/unique enforced | Informational only — which is why the dq checks (`error__dim_fan_one_current`, `error__fact_email_engagement_unique`) exist rather than trusting the schema |
| Identity columns | `GENERATED ALWAYS AS IDENTITY` | `IDENTITY(1,1)`, values not guaranteed gap-free |
| `generate_series` in CTAS | Fine | Leader-node-only: build `dim_date` from a numbers table (`SELECT row_number() OVER () ...` against any large table) |
| `FILTER (WHERE ...)` | Supported (avoided anyway) | Unsupported — all marts already use `CASE WHEN` sums |
| Maintenance | autovacuum | `VACUUM` + `ANALYZE` scheduled (auto in Serverless, still worth monitoring `SVV_TABLE_INFO` skew/unsorted) |
| Ephemeral compute | n/a | Serverless bills per RPU-second with an 8-RPU floor — the reason the module stays unapplied ($0 rule) |

What does **not** change: schema layout, the model runner and every model's
shape (DROP+CTAS full rebuilds and the two incremental patterns), the dq
check SQL, the unification interface tables, and all `boto3` lake code
(drop `FANUNI_S3_ENDPOINT_URL` and it targets real S3).
