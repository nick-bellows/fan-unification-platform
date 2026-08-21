"""End-to-end ingestion against the real compose stack.

Requires `docker compose up -d` (postgres, minio, prefect, salesforce-mock).
Without the stack the module skips locally; CI sets FANUNI_REQUIRE_STACK=1 so
a missing stack fails instead of silently skipping.

Tests in this module are ordered stages of one pipeline story — later tests
assume earlier ones ran (pytest executes them in definition order).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg
import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]


def _scalar(conn: psycopg.Connection[Any], sql: str) -> int:
    row = conn.execute(sql).fetchone()
    assert row is not None
    return int(row[0])


def test_stage1_first_ingest_loads_everything(
    fresh_db: psycopg.Connection[Any], manifest: dict[str, Any]
) -> None:
    from fanuni.pipeline.flows import ingest_file_sources, ingest_salesforce

    counts = ingest_salesforce()
    expected = manifest["counts"]
    assert counts["crm_contacts"] == expected["crm_contacts"]
    assert counts["crm_opportunities"] == expected["crm_opportunities"]

    file_counts = ingest_file_sources()
    assert file_counts["ticketing_orders"] == expected["ticket_orders"]
    assert file_counts["merch_order_items"] == expected["merch_line_rows"]
    assert file_counts["email_subscribers"] == expected["email_subscribers"]
    assert file_counts["email_events"] == expected["email_events"]
    assert file_counts["email_campaigns"] == expected["campaigns"]
    assert file_counts["fixtures"] == expected["fixtures"]

    assert _scalar(fresh_db, "SELECT count(*) FROM raw.crm_contacts") == expected["crm_contacts"]
    assert _scalar(fresh_db, "SELECT count(*) FROM raw.quarantine") == 0

    # The CRM watermark advanced to the max modstamp extracted.
    watermark = fresh_db.execute(
        "SELECT watermark_value FROM ops.watermarks WHERE source = 'crm.Contact'"
    ).fetchone()
    assert watermark is not None
    top = fresh_db.execute(
        "SELECT max(payload->>'SystemModstamp') FROM raw.crm_contacts"
    ).fetchone()
    assert top is not None and watermark[0] == top[0]


def test_stage2_rerun_is_a_no_op(fresh_db: psycopg.Connection[Any]) -> None:
    from fanuni.pipeline.flows import ingest_file_sources, ingest_salesforce

    before = _scalar(fresh_db, "SELECT count(*) FROM raw.crm_contacts")
    assert all(v == 0 for v in ingest_salesforce().values())
    assert all(v == 0 for v in ingest_file_sources().values())
    assert _scalar(fresh_db, "SELECT count(*) FROM raw.crm_contacts") == before


def test_stage3_schema_drift_landed_both_forms(fresh_db: psycopg.Connection[Any]) -> None:
    pre = _scalar(
        fresh_db, "SELECT count(*) FROM raw.merch_order_items WHERE payload ? 'billing_zip'"
    )
    post = _scalar(
        fresh_db,
        "SELECT count(*) FROM raw.merch_order_items WHERE payload ? 'billing_postal_code'",
    )
    assert pre > 0 and post > 0


def test_stage4_bad_rows_quarantine_with_reason(fresh_db: psycopg.Connection[Any]) -> None:
    from fanuni.pipeline.flows import ingest_file_sources

    target = sorted((REPO_ROOT / "data" / "dropzone" / "ticketing").glob("orders_*.jsonl"))[0]
    good_rows = _scalar(fresh_db, "SELECT count(*) FROM raw.ticketing_orders")
    with target.open("a", encoding="utf-8") as f:
        f.write(
            '{"order_id": "T-999999", "match_id": "MTCH-0001", '
            '"purchased_at": "2026-01-01T00:00:00Z", "qty": 99, "total": 10.0, '
            '"purchaser_name": "Bad Row", "purchaser_email": "bad@example.com"}\n'
        )
    counts = ingest_file_sources(sources=["ticketing_orders"])
    assert counts["ticketing_orders"] > 0  # the changed file reloaded

    quarantined = fresh_db.execute(
        "SELECT payload->>'order_id', reason FROM raw.quarantine WHERE source = 'ticketing_orders'"
    ).fetchall()
    assert [q[0] for q in quarantined] == ["T-999999"]
    assert "qty" in quarantined[0][1]
    # No duplication of the good rows despite the reload.
    assert _scalar(fresh_db, "SELECT count(*) FROM raw.ticketing_orders") == good_rows

    # Correct the file (drop the bad row) and re-ingest: the stale quarantine
    # entry must clear — a corrected file with zero rejects leaves no residue.
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    target.write_text("".join(line for line in lines if "T-999999" not in line), encoding="utf-8")
    ingest_file_sources(sources=["ticketing_orders"])
    assert (
        _scalar(
            fresh_db,
            "SELECT count(*) FROM raw.quarantine WHERE source = 'ticketing_orders'",
        )
        == 0
    )
    assert _scalar(fresh_db, "SELECT count(*) FROM raw.ticketing_orders") == good_rows


def test_stage5_backfill_window_filters_files(fresh_db: psycopg.Connection[Any]) -> None:
    from fanuni.pipeline.flows import ingest_file_sources

    counts = ingest_file_sources(sources=["ticketing_orders"], start_month="2099-01", force=True)
    assert counts["ticketing_orders"] == 0


def test_stage6_lake_holds_raw_objects(stack: Any) -> None:
    from fanuni.pipeline.lake import list_keys, s3_client

    client = s3_client(stack)
    assert list_keys(client, stack.lake_bucket, "raw/crm/crm_contacts/")
    assert list_keys(client, stack.lake_bucket, "raw/ticketing/")
