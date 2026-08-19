from datetime import UTC, datetime

from fanuni.unification.evaluate import pair_metrics, tag_breakdown
from fanuni.unification.nicknames import canonical_first_name
from fanuni.unification.probabilistic import (
    ProbabilisticResult,
    ScoredEdge,
    combine,
    prepare_frame,
)
from fanuni.unification.records import IdentityRecord


def _record(ref: str, first: str = "Sam") -> IdentityRecord:
    source, _, record_id = ref.partition(":")
    return IdentityRecord(
        source_system=source,
        source_record_id=record_id,
        first_name=first,
        last_name="Example",
        email=None,
        phone=None,
        city=None,
        state=None,
        zip_code=None,
        dob=None,
        birth_year=None,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_canonical_first_name() -> None:
    assert canonical_first_name("bill") == "william"
    assert canonical_first_name("william") == "william"
    assert canonical_first_name("zelda") == "zelda"
    assert canonical_first_name(None) is None


def test_prepare_frame_folds_and_canonicalizes() -> None:
    frame = prepare_frame([_record("crm:1", first="Bill"), _record("crm:2", first="José")])
    assert list(frame["first_name_c"]) == ["william", "jose"]
    assert list(frame["unique_id"]) == ["crm:1", "crm:2"]


def test_combine_labels_probabilistic_additions() -> None:
    records = [_record("crm:1"), _record("email:2"), _record("merch:3")]
    deterministic = {"crm:1": ["crm:1", "email:2"], "merch:3": ["merch:3"]}
    prob = ProbabilisticResult(edges=[ScoredEdge("crm:1", "merch:3", 0.97)], review_band=[])
    combined = combine(records, deterministic, prob)
    assert len(combined.clusters) == 1
    assert combined.method_by_ref["crm:1"] == "deterministic"
    assert combined.method_by_ref["email:2"] == "deterministic"
    assert combined.method_by_ref["merch:3"] == "probabilistic"
    assert combined.score_by_ref["merch:3"] == 0.97


def test_pair_metrics_hand_calculation() -> None:
    # Truth: entity A = {a1, a2, a3}; entity B = {b1}. True pairs = 3.
    truth = {
        "crm:a1": ("A", []),
        "crm:a2": ("A", ["typo"]),
        "email:a3": ("A", []),
        "email:b1": ("B", []),
    }
    # Prediction: {a1, a2} together (1 TP), {a3, b1} wrongly merged (1 FP).
    clusters = {"x": ["crm:a1", "crm:a2"], "y": ["email:a3", "email:b1"]}
    metrics, fp_pairs, fn_pairs = pair_metrics(clusters, truth)
    assert metrics.tp == 1 and metrics.fp == 1 and metrics.fn == 2
    assert metrics.precision == 0.5
    assert round(metrics.recall, 4) == round(1 / 3, 4)

    rows = tag_breakdown(truth, clusters, fp_pairs, fn_pairs)
    typo = next(r for r in rows if r["tag"] == "typo")
    # True pairs touching the typo record: (a1,a2), (a2,a3) -> one found.
    assert typo["true_pairs"] == 2
    assert typo["pair_recall"] == 0.5
