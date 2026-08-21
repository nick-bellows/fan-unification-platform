"""Warehouse loads: COPY into raw, delete+insert keyed by source file.

Replaying the same object is a clean replace, never a duplication — the
idempotency contract the integration tests assert. Table names come only from
the RAW_TABLES mapping (never user input).
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

RAW_TABLES: dict[str, str] = {
    "crm_contacts": "raw.crm_contacts",
    "crm_opportunities": "raw.crm_opportunities",
    "ticketing_orders": "raw.ticketing_orders",
    "merch_order_items": "raw.merch_order_items",
    "email_subscribers": "raw.email_subscribers",
    "email_events": "raw.email_events",
    "email_campaigns": "raw.email_campaigns",
    "fixtures": "raw.fixtures",
}


def replace_batch(
    conn: psycopg.Connection[Any],
    source_key: str,
    rows: list[dict[str, Any]],
    batch_id: str,
    source_file: str,
) -> int:
    table = RAW_TABLES[source_key]
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {table} WHERE source_file = %s",
            (source_file,),
        )
        with cur.copy(f"COPY {table} (payload, batch_id, source_file) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((Jsonb(row), batch_id, source_file))
    return len(rows)


def quarantine_rows(
    conn: psycopg.Connection[Any],
    source_key: str,
    rejects: list[tuple[dict[str, Any], str]],
    batch_id: str,
    source_file: str,
) -> int:
    # Always clear the file's previous quarantine rows first: a corrected
    # file that now has zero rejects must not leave stale quarantine behind.
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM raw.quarantine WHERE source = %s AND source_file = %s",
            (source_key, source_file),
        )
        if not rejects:
            return 0
        with cur.copy(
            "COPY raw.quarantine (source, payload, reason, batch_id, source_file) FROM STDIN"
        ) as copy:
            for row, reason in rejects:
                copy.write_row((source_key, Jsonb(row), reason, batch_id, source_file))
    return len(rejects)
