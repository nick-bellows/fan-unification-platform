"""Ground-truth evaluation of unification, and the regression floors.

Runs after test_transform on the same session dataset. The floors are set
just below the first honestly observed numbers for the CI dataset (seed 1234,
800 fans) — see eval/results/ for the committed full-scale report. If a change
drops a metric through a floor, that's a regression to explain, not a floor to
lower quietly (eval-honesty rule; bump UNIFIER_VERSION with evidence instead).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg
import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]

# Floors for the CI dataset, set just below the first observed run
# (deterministic 0.9171/0.9309, full 0.8829/0.9956 — 2026-08-19); see module
# docstring for the rules about changing them.
FLOORS = {
    "deterministic": {"precision": 0.89, "recall": 0.90},
    "full": {"precision": 0.85, "recall": 0.97},
}


@pytest.fixture(scope="module")
def eval_report(
    fresh_db: psycopg.Connection[Any], manifest: dict[str, Any], tmp_path_factory: Any
) -> dict[str, Any]:
    from fanuni.unification.evaluate import run_eval

    out = tmp_path_factory.mktemp("eval")
    report: dict[str, Any] = run_eval(
        fresh_db,
        truth_path=REPO_ROOT / "data" / "truth" / "record_map.csv",
        out_dir=out / "results",
        review_dir=out / "review",
    )
    return report


def test_eval_covers_all_records(eval_report: dict[str, Any], manifest: dict[str, Any]) -> None:
    assert eval_report["records_evaluated"] == manifest["counts"]["truth_records"]


def test_full_recall_beats_deterministic_baseline(eval_report: dict[str, Any]) -> None:
    det = eval_report["variants"]["deterministic"]["metrics"]
    full = eval_report["variants"]["full"]["metrics"]
    # The probabilistic pass exists to find links exact rules cannot; it must
    # never lose links the deterministic pass already had.
    assert full["recall"] >= det["recall"]
    assert full["tp"] >= det["tp"]


def test_metric_floors(eval_report: dict[str, Any]) -> None:
    for variant, floors in FLOORS.items():
        metrics = eval_report["variants"][variant]["metrics"]
        assert metrics["precision"] >= floors["precision"], (
            f"{variant} precision {metrics['precision']} fell through floor"
        )
        assert metrics["recall"] >= floors["recall"], (
            f"{variant} recall {metrics['recall']} fell through floor"
        )


def test_eval_lands_on_ops_tables(
    eval_report: dict[str, Any], fresh_db: psycopg.Connection[Any]
) -> None:
    rows = fresh_db.execute(
        "SELECT variant, pair_precision, pair_recall FROM ops.linkage_eval ORDER BY id DESC LIMIT 2"
    ).fetchall()
    assert {r[0] for r in rows} == {"deterministic", "full"}
    tags = fresh_db.execute("SELECT count(*) FROM ops.linkage_eval_tags").fetchone()
    assert tags is not None and tags[0] > 0
