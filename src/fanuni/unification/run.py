"""Unification orchestration: records -> clusters -> golden tables."""

from __future__ import annotations

from typing import Any

import psycopg

from fanuni.unification.deterministic import deterministic_clusters
from fanuni.unification.golden import GoldenFan, XrefRow, build_golden, fan_id_for
from fanuni.unification.records import IdentityRecord, fetch_identity_records


def materialize(
    records: list[IdentityRecord],
    clusters: dict[str, list[str]],
    method_by_ref: dict[str, str] | None = None,
    score_by_ref: dict[str, float] | None = None,
) -> tuple[list[XrefRow], list[GoldenFan]]:
    by_ref = {r.ref: r for r in records}
    xref: list[XrefRow] = []
    golden: list[GoldenFan] = []
    for members in clusters.values():
        fan_id = fan_id_for(members)
        for ref in members:
            source_system, _, source_record_id = ref.partition(":")
            if method_by_ref is not None:
                method = method_by_ref[ref]
            else:
                method = "singleton" if len(members) == 1 else "deterministic"
            score = (score_by_ref or {}).get(ref) if method == "probabilistic" else None
            xref.append(XrefRow(source_system, source_record_id, fan_id, method, score))
        golden.append(build_golden([by_ref[m] for m in members]))
    return xref, golden


def run_unification(conn: psycopg.Connection[Any], mode: str = "full") -> dict[str, int]:
    """mode='deterministic' is the M3 baseline; 'full' adds the Splink pass."""
    from fanuni.unification.golden import write_identity_tables

    records = fetch_identity_records(conn)
    det = deterministic_clusters(records)
    review_band = 0
    if mode == "full":
        from fanuni.unification.probabilistic import combine, probabilistic_edges

        prob = probabilistic_edges(records)
        combined = combine(records, det, prob)
        clusters = combined.clusters
        xref, golden = materialize(records, clusters, combined.method_by_ref, combined.score_by_ref)
        review_band = len(prob.review_band)
    elif mode == "deterministic":
        xref, golden = materialize(records, det)
    else:
        raise ValueError(f"unknown unification mode: {mode}")

    write_identity_tables(conn, xref, golden)
    return {
        "records": len(records),
        "fans": len(golden),
        "multi_record_fans": sum(1 for g in golden if g.record_count > 1),
        "review_band": review_band,
    }
