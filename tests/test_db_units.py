"""Run-status bookkeeping that must not depend on a live database."""

from __future__ import annotations

from typing import Any

from fanuni.pipeline.db import mark_run_failed


class _Conn:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def rollback(self) -> None:
        self.calls.append("rollback")

    def execute(self, sql: str, params: Any = None) -> None:
        self.calls.append(f"execute:{params[0]}")

    def commit(self) -> None:
        self.calls.append("commit")


def test_mark_run_failed_rolls_back_before_writing_status() -> None:
    # After a failed statement the transaction is aborted; updating the run
    # row first would itself raise and bury the original error.
    conn = _Conn()
    mark_run_failed(conn, "run-1")  # type: ignore[arg-type]
    assert conn.calls == ["rollback", "execute:failed", "commit"]
