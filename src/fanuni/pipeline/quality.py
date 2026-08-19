"""Data-quality gates: SQL assertions that return VIOLATING rows.

warehouse/checks/<severity>__<name>.sql — zero rows returned means pass.
error-severity failures fail the run (and CI); warns are recorded and
surfaced on the ops dashboard. Results always land in ops.dq_results.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg


@dataclass(frozen=True)
class CheckResult:
    name: str
    severity: str
    passed: bool
    failed_rows: int
    detail: str | None


class QualityGateError(RuntimeError):
    pass


def run_checks(conn: psycopg.Connection[Any], checks_dir: Path, run_id: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    for sql_file in sorted(checks_dir.glob("*.sql")):
        severity, sep, name = sql_file.stem.partition("__")
        if not sep or severity not in ("error", "warn"):
            raise ValueError(f"check file not named severity__name.sql: {sql_file}")
        violations = conn.execute(sql_file.read_text(encoding="utf-8")).fetchall()
        passed = len(violations) == 0
        detail = None if passed else "; ".join(str(v) for v in violations[:3])
        conn.execute(
            """
            INSERT INTO ops.dq_results (run_id, check_name, severity, passed, failed_rows, detail)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (run_id, name, severity, passed, len(violations), detail),
        )
        conn.commit()
        results.append(CheckResult(name, severity, passed, len(violations), detail))
    return results


def enforce_gate(results: list[CheckResult]) -> None:
    errors = [r for r in results if r.severity == "error" and not r.passed]
    if errors:
        summary = "; ".join(f"{r.name} ({r.failed_rows} rows)" for r in errors)
        raise QualityGateError(f"data-quality gate failed: {summary}")
