"""Warehouse connection and ops-table helpers.

All audit writes go through here so every flow leaves the same trail:
a row in ops.pipeline_runs, a row in ops.load_audit per object loaded.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from fanuni.config import Settings


def connect(settings: Settings) -> psycopg.Connection[Any]:
    return psycopg.connect(settings.database_url)


def run_sql_dir(conn: psycopg.Connection[Any], directory: Path) -> list[str]:
    """Execute every .sql file in name order, one transaction per file."""
    executed: list[str] = []
    for sql_file in sorted(directory.glob("*.sql")):
        conn.execute(sql_file.read_text(encoding="utf-8"))
        conn.commit()
        executed.append(sql_file.name)
    return executed


def start_run(conn: psycopg.Connection[Any], flow_name: str, parameters: dict[str, Any]) -> str:
    run_id = f"{flow_name}-{uuid.uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO ops.pipeline_runs (run_id, flow_name, parameters) VALUES (%s, %s, %s)",
        (run_id, flow_name, Jsonb(parameters)),
    )
    conn.commit()
    return run_id


def finish_run(conn: psycopg.Connection[Any], run_id: str, status: str) -> None:
    conn.execute(
        "UPDATE ops.pipeline_runs SET status = %s, finished_at = now() WHERE run_id = %s",
        (status, run_id),
    )
    conn.commit()


def audit_load(
    conn: psycopg.Connection[Any],
    run_id: str,
    source: str,
    object_key: str,
    target_table: str,
    rows_loaded: int,
    rows_rejected: int,
) -> None:
    conn.execute(
        """
        INSERT INTO ops.load_audit
          (run_id, source, object_key, target_table, rows_loaded, rows_rejected)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (run_id, source, object_key, target_table, rows_loaded, rows_rejected),
    )


def get_watermark(conn: psycopg.Connection[Any], source: str) -> str | None:
    row = conn.execute(
        "SELECT watermark_value FROM ops.watermarks WHERE source = %s", (source,)
    ).fetchone()
    return row[0] if row else None


def set_watermark(conn: psycopg.Connection[Any], source: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO ops.watermarks (source, watermark_value, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (source)
        DO UPDATE SET watermark_value = EXCLUDED.watermark_value, updated_at = now()
        """,
        (source, value),
    )


def ingested_sha(conn: psycopg.Connection[Any], source: str, file_name: str) -> str | None:
    row = conn.execute(
        "SELECT sha256 FROM ops.ingested_files WHERE source = %s AND file_name = %s",
        (source, file_name),
    ).fetchone()
    return row[0] if row else None


def record_ingested_file(
    conn: psycopg.Connection[Any],
    source: str,
    file_name: str,
    sha256: str,
    object_key: str,
    rows: int,
) -> None:
    conn.execute(
        """
        INSERT INTO ops.ingested_files (source, file_name, sha256, object_key, rows)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source, file_name)
        DO UPDATE SET sha256 = EXCLUDED.sha256, object_key = EXCLUDED.object_key,
                      rows = EXCLUDED.rows, ingested_at = now()
        """,
        (source, file_name, sha256, object_key, rows),
    )
