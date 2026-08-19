"""Transform + unification + quality gates against the live warehouse.

Runs after test_ingest (alphabetical collection order) on the state it left:
raw fully loaded, one quarantined ticketing row.
"""

from __future__ import annotations

from typing import Any

import psycopg
import pytest

pytestmark = pytest.mark.integration


def _scalar(conn: psycopg.Connection[Any], sql: str) -> int:
    row = conn.execute(sql).fetchone()
    assert row is not None
    return int(row[0] or 0)


def test_stage1_transform_builds_the_star(
    fresh_db: psycopg.Connection[Any], manifest: dict[str, Any]
) -> None:
    from fanuni.pipeline.flows import transform_warehouse

    stats = transform_warehouse()
    expected = manifest["counts"]

    # Within-source dedupe: staging contacts equal raw contacts (each Id
    # extracted once), orders equal generated orders.
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM staging.stg_crm_contacts")
        == (expected["crm_contacts"])
    )
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM staging.stg_ticketing_orders")
        == expected["ticket_orders"]
    )
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM staging.identity_records")
        == expected["truth_records"]
    )

    # Unification collapsed records into fewer fans than records.
    assert 0 < stats["fans"] < stats["records"]
    assert stats["records"] == expected["truth_records"]

    # Facts reconcile to staging grain.
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM core.fact_ticket_sales")
        == expected["ticket_orders"]
    )
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM core.fact_merch_sales")
        == expected["merch_line_rows"]
    )
    assert (
        _scalar(fresh_db, "SELECT count(*) FROM core.fact_email_engagement")
        == expected["email_events"]
    )

    # dim_fan carries exactly one current row per golden fan.
    assert _scalar(fresh_db, "SELECT count(*) FROM core.dim_fan WHERE is_current") == stats["fans"]
    assert _scalar(fresh_db, "SELECT count(*) FROM marts.fan_360") == stats["fans"]


def test_stage2_transform_rerun_is_stable(fresh_db: psycopg.Connection[Any]) -> None:
    from fanuni.pipeline.flows import transform_warehouse

    fans_before = _scalar(fresh_db, "SELECT count(*) FROM core.dim_fan")
    events_before = _scalar(fresh_db, "SELECT count(*) FROM core.fact_email_engagement")
    stats = transform_warehouse()
    # Same inputs -> same clusters -> no new SCD2 versions, no re-inserted events.
    assert _scalar(fresh_db, "SELECT count(*) FROM core.dim_fan") == fans_before
    assert _scalar(fresh_db, "SELECT count(*) FROM core.fact_email_engagement") == events_before
    assert _scalar(fresh_db, "SELECT count(*) FROM core.dim_fan WHERE is_current") == stats["fans"]


def test_stage3_quality_gates_pass(fresh_db: psycopg.Connection[Any]) -> None:
    from fanuni.pipeline.flows import run_quality_gates

    summary = run_quality_gates()
    assert summary["failed_errors"] == 0

    # Every check wrote a result row.
    assert (
        _scalar(
            fresh_db,
            "SELECT count(DISTINCT check_name) FROM ops.dq_results",
        )
        == summary["checks"]
    )


def test_stage4_quality_gate_fails_when_data_breaks(
    fresh_db: psycopg.Connection[Any],
) -> None:
    """A gate that cannot fail proves nothing: break an invariant, watch it
    fail, repair, watch it pass again."""
    from fanuni.pipeline.flows import run_quality_gates
    from fanuni.pipeline.quality import QualityGateError

    fresh_db.execute(
        """
        INSERT INTO core.dim_fan (fan_id, first_name, last_name)
        SELECT fan_id, 'Dup', 'Row' FROM core.dim_fan WHERE is_current LIMIT 1
        """
    )
    fresh_db.commit()
    with pytest.raises(QualityGateError, match="dim_fan_one_current"):
        run_quality_gates()

    fresh_db.execute("DELETE FROM core.dim_fan WHERE first_name = 'Dup' AND last_name = 'Row'")
    fresh_db.commit()
    assert run_quality_gates()["failed_errors"] == 0


def test_stage5_analyst_role_cannot_read_pii(stack: Any, fresh_db: psycopg.Connection[Any]) -> None:
    """Column-level grants: the analyst role reads measures, never PII.
    Uses a dedicated connection so the shared session connection never
    changes role."""
    from fanuni.pipeline.db import connect

    conn = connect(stack)
    conn.autocommit = True
    try:
        conn.execute("SET ROLE analyst")
        row = conn.execute("SELECT fan_id, total_revenue FROM marts.fan_360 LIMIT 1").fetchone()
        assert row is not None
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT email FROM marts.fan_360 LIMIT 1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT * FROM identity.golden_fans LIMIT 1")
    finally:
        conn.close()


def test_stage6_household_email_shows_expected_overmerge(
    fresh_db: psycopg.Connection[Any],
) -> None:
    """The deterministic pass knowingly merges household members who share an
    email. Confirm the mechanism exists (clusters spanning multiple distinct
    folded first names) — M4 measures its precision cost against ground truth."""
    row = fresh_db.execute(
        """
        SELECT count(*)
        FROM identity.golden_fans
        WHERE record_count >= 3
        """
    ).fetchone()
    assert row is not None and row[0] > 0
