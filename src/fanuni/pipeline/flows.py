"""Prefect flows: extraction and load.

Network-touching steps are tasks with retries/backoff; warehouse writes happen
in the flow body on one connection so each run leaves a single, coherent audit
trail (ops.pipeline_runs / ops.load_audit) that commits or fails together per
object.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger, task

from fanuni.config import Settings, load_settings
from fanuni.pipeline import db
from fanuni.pipeline.contracts import validate_rows
from fanuni.pipeline.lake import ensure_bucket, put_bytes, s3_client
from fanuni.pipeline.load import RAW_TABLES, quarantine_rows, replace_batch
from fanuni.pipeline.salesforce import SalesforceClient, build_soql

SF_OBJECTS: tuple[tuple[str, str], ...] = (
    ("Contact", "crm_contacts"),
    ("Opportunity", "crm_opportunities"),
)

_MONTH_IN_NAME = re.compile(r"_(\d{4}-\d{2})\.(?:csv|jsonl)$")


@dataclass(frozen=True)
class FileSource:
    name: str  # key into RAW_TABLES
    subdir: str
    pattern: str
    fmt: str  # jsonl | csv


FILE_SOURCES: tuple[FileSource, ...] = (
    FileSource("ticketing_orders", "ticketing", "orders_*.jsonl", "jsonl"),
    FileSource("merch_order_items", "merch", "orders_*.csv", "csv"),
    FileSource("email_subscribers", "email", "subscribers_*.csv", "csv"),
    FileSource("email_events", "email", "events_*.jsonl", "jsonl"),
    FileSource("email_campaigns", "email", "campaigns.csv", "csv"),
    FileSource("fixtures", "fixtures", "fixtures.csv", "csv"),
)


def batch_month(file_name: str) -> str | None:
    match = _MONTH_IN_NAME.search(file_name)
    return match.group(1) if match else None


def parse_rows(fmt: str, body: bytes) -> list[dict[str, Any]]:
    text = body.decode("utf-8")
    if fmt == "jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return [dict(r) for r in csv.DictReader(io.StringIO(text))]


@task(retries=3, retry_delay_seconds=[2, 5, 15])
def fetch_sobject(settings: Settings, sobject: str, after: str | None) -> list[dict[str, Any]]:
    client = SalesforceClient(
        settings.sf_base_url,
        settings.sf_client_id,
        settings.sf_client_secret.get_secret_value(),
    )
    try:
        records = client.query_all(build_soql(sobject, after))
    finally:
        client.close()
    for record in records:
        record.pop("attributes", None)
    return records


@task(retries=3, retry_delay_seconds=[2, 5, 15])
def upload_to_lake(settings: Settings, key: str, body: bytes) -> None:
    client = s3_client(settings)
    ensure_bucket(client, settings.lake_bucket)
    put_bytes(client, settings.lake_bucket, key, body)


@flow(name="ingest-salesforce")
def ingest_salesforce(full_refresh: bool = False) -> dict[str, int]:
    """Watermark-incremental extraction of Contact/Opportunity into raw."""
    logger = get_run_logger()
    settings = load_settings()
    conn = db.connect(settings)
    run_id = db.start_run(conn, "ingest-salesforce", {"full_refresh": full_refresh})
    counts: dict[str, int] = {}
    try:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        for sobject, source_key in SF_OBJECTS:
            watermark_key = f"crm.{sobject}"
            after = None if full_refresh else db.get_watermark(conn, watermark_key)
            records = fetch_sobject(settings, sobject, after)
            if not records:
                logger.info("%s: nothing new past watermark %s", sobject, after)
                counts[source_key] = 0
                continue
            key = f"raw/crm/{source_key}/extracted={stamp}/records.jsonl"
            body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
            upload_to_lake(settings, key, body.encode("utf-8"))

            good, rejects = validate_rows(source_key, records)
            loaded = replace_batch(conn, source_key, good, batch_id=key, source_file=key)
            quarantine_rows(conn, source_key, rejects, batch_id=key, source_file=key)
            db.audit_load(
                conn, run_id, source_key, key, RAW_TABLES[source_key], loaded, len(rejects)
            )
            # Advance the watermark only over ACCEPTED rows: advancing past a
            # quarantined record would mean its corrected version (with an
            # unchanged modstamp) could never be re-extracted incrementally.
            if good:
                db.set_watermark(conn, watermark_key, max(r["SystemModstamp"] for r in good))
            conn.commit()
            counts[source_key] = loaded
            logger.info("%s: loaded %d rows (%d quarantined)", sobject, loaded, len(rejects))
        db.finish_run(conn, run_id, "completed")
    except Exception:
        conn.rollback()
        db.finish_run(conn, run_id, "failed")
        raise
    finally:
        conn.close()
    return counts


@flow(name="transform-warehouse")
def transform_warehouse(unify_mode: str = "full") -> dict[str, Any]:
    """staging models -> unification -> core/marts models, one audit trail."""
    from fanuni.pipeline.sql_runner import run_models
    from fanuni.unification.run import run_unification

    logger = get_run_logger()
    settings = load_settings()
    models_dir = Path(settings.warehouse_dir) / "models"
    conn = db.connect(settings)
    run_id = db.start_run(conn, "transform-warehouse", {"unify_mode": unify_mode})
    try:
        staging = run_models(conn, models_dir, run_id, layers=["staging"])
        unify_stats = run_unification(conn, mode=unify_mode)
        logger.info("unified %d records into %d fans", unify_stats["records"], unify_stats["fans"])
        downstream = run_models(conn, models_dir, run_id, layers=["core", "marts"])
        # Marts were just rebuilt, which dropped the analyst role's grants.
        grants = Path(settings.warehouse_dir) / "grants.sql"
        conn.execute(grants.read_text(encoding="utf-8"))
        conn.commit()
        db.finish_run(conn, run_id, "completed")
        return {"models_run": len(staging) + len(downstream), **unify_stats}
    except Exception:
        conn.rollback()
        db.finish_run(conn, run_id, "failed")
        raise
    finally:
        conn.close()


@flow(name="quality-gates")
def run_quality_gates() -> dict[str, int]:
    """Run every SQL assertion; error-severity failures raise."""
    from fanuni.pipeline.quality import enforce_gate, run_checks

    logger = get_run_logger()
    settings = load_settings()
    conn = db.connect(settings)
    run_id = db.start_run(conn, "quality-gates", {})
    try:
        results = run_checks(conn, Path(settings.warehouse_dir) / "checks", run_id)
        for result in results:
            if not result.passed:
                logger.warning(
                    "%s check failed: %s (%d rows)",
                    result.severity,
                    result.name,
                    result.failed_rows,
                )
        db.finish_run(conn, run_id, "completed")
        summary = {
            "checks": len(results),
            "failed_errors": sum(1 for r in results if r.severity == "error" and not r.passed),
            "failed_warns": sum(1 for r in results if r.severity == "warn" and not r.passed),
        }
        enforce_gate(results)
        return summary
    except Exception:
        db.finish_run(conn, run_id, "failed")
        raise
    finally:
        conn.close()


@flow(name="nightly-pipeline")
def nightly_pipeline(full_refresh: bool = False, force: bool = False) -> dict[str, Any]:
    """The production run: ingest everything, transform, gate."""
    ingest_counts = ingest_salesforce(full_refresh=full_refresh)
    file_counts = ingest_file_sources(force=force)
    transform_stats = transform_warehouse()
    gate_stats = run_quality_gates()
    return {
        "ingested": {**ingest_counts, **file_counts},
        "transform": transform_stats,
        "quality": gate_stats,
    }


@flow(name="ingest-file-sources")
def ingest_file_sources(
    sources: list[str] | None = None,
    start_month: str | None = None,
    end_month: str | None = None,
    force: bool = False,
) -> dict[str, int]:
    """Dropzone files -> lake -> raw. Re-runs skip unchanged files by sha256;
    start/end month bound a backfill; force reloads regardless."""
    logger = get_run_logger()
    settings = load_settings()
    conn = db.connect(settings)
    parameters = {
        "sources": sources,
        "start_month": start_month,
        "end_month": end_month,
        "force": force,
    }
    run_id = db.start_run(conn, "ingest-file-sources", parameters)
    counts: dict[str, int] = {}
    try:
        for source in FILE_SOURCES:
            if sources and source.name not in sources:
                continue
            counts[source.name] = 0
            directory = Path(settings.dropzone_dir) / source.subdir
            for path in sorted(directory.glob(source.pattern)):
                month = batch_month(path.name)
                if month and start_month and month < start_month:
                    continue
                if month and end_month and month > end_month:
                    continue
                body = path.read_bytes()
                sha = hashlib.sha256(body).hexdigest()
                if not force and db.ingested_sha(conn, source.name, path.name) == sha:
                    continue
                key = f"raw/{source.subdir}/{source.name}/{path.name}"
                upload_to_lake(settings, key, body)

                rows = parse_rows(source.fmt, body)
                good, rejects = validate_rows(source.name, rows)
                loaded = replace_batch(conn, source.name, good, batch_id=path.name, source_file=key)
                quarantine_rows(conn, source.name, rejects, batch_id=path.name, source_file=key)
                db.audit_load(
                    conn, run_id, source.name, key, RAW_TABLES[source.name], loaded, len(rejects)
                )
                db.record_ingested_file(conn, source.name, path.name, sha, key, loaded)
                conn.commit()
                counts[source.name] += loaded
                if rejects:
                    logger.warning("%s: quarantined %d rows", path.name, len(rejects))
        db.finish_run(conn, run_id, "completed")
    except Exception:
        conn.rollback()
        db.finish_run(conn, run_id, "failed")
        raise
    finally:
        conn.close()
    return counts
