"""Probabilistic pass: Splink 4 (Fellegi-Sunter, EM-trained) on DuckDB.

Runs on the same identity records as the deterministic pass and returns scored
pairwise edges. The DuckDB engine is Splink's first-class backend (ADR 0004);
results feed the same union-find, so the deterministic edges always survive.

UNIFIER_VERSION stamps every eval report; bump it whenever thresholds,
comparisons, blocking, or training change, and land the regenerated eval in
the same commit (the eval-honesty rule).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from fanuni.unification.nicknames import canonical_first_name
from fanuni.unification.records import IdentityRecord, fold

# 1 = deterministic only (M3); 2 = + Splink pass at auto-merge 0.90;
# 3 = operating point moved to 0.9999 after the full-scale threshold sweep
# (eval/results/threshold_sweep.md) showed FS posteriors saturate and v2's
# threshold lost to the deterministic baseline on F1 at 5k fans.
UNIFIER_VERSION = "3"


@dataclass(frozen=True)
class ScoredEdge:
    ref_l: str
    ref_r: str
    probability: float


@dataclass(frozen=True)
class ProbabilisticResult:
    edges: list[ScoredEdge]  # probability >= auto_merge_threshold
    review_band: list[ScoredEdge]  # review_threshold <= p < auto_merge_threshold


@dataclass(frozen=True)
class UnifyConfig:
    # Operating point chosen from the measured precision/recall curve at full
    # scale (eval/results/threshold_sweep.md): with many agreeing fields the
    # Fellegi-Sunter posterior saturates near 1.0, so the useful separation
    # between real matches and household/name-coincidence pairs happens above
    # 0.999. The band below the auto-merge threshold goes to clerical review.
    auto_merge_threshold: float = 0.9999
    review_threshold: float = 0.999
    em_max_pairs: float = 4e6
    seed: int = 42


def prepare_frame(records: list[IdentityRecord]) -> pd.DataFrame:
    """Match-ready projection: folded names, canonical first name, birth year."""
    rows = []
    for r in records:
        first = fold(r.first_name)
        rows.append(
            {
                "unique_id": r.ref,
                "first_name_c": canonical_first_name(first),
                "last_name_f": fold(r.last_name),
                "email": r.email,
                "phone": r.phone,
                "zip": r.zip_code,
                "birth_year": str(r.birth_year) if r.birth_year else None,
            }
        )
    return pd.DataFrame(rows)


def _splink_settings() -> Any:
    import splink.comparison_library as cl
    from splink import SettingsCreator, block_on

    return SettingsCreator(
        link_type="dedupe_only",
        comparisons=[
            cl.JaroWinklerAtThresholds("first_name_c", [0.92, 0.8]),
            cl.JaroWinklerAtThresholds("last_name_f", [0.92, 0.8]),
            cl.LevenshteinAtThresholds("email", 2),
            cl.ExactMatch("phone"),
            cl.ExactMatch("zip"),
            cl.ExactMatch("birth_year"),
        ],
        blocking_rules_to_generate_predictions=[
            block_on("email"),
            block_on("phone"),
            block_on("last_name_f", "zip"),
            block_on("first_name_c", "last_name_f"),
            block_on("birth_year", "zip"),
        ],
        retain_intermediate_calculation_columns=False,
    )


def probabilistic_edges(
    records: list[IdentityRecord], config: UnifyConfig | None = None
) -> ProbabilisticResult:
    from splink import DuckDBAPI, Linker, block_on

    config = config or UnifyConfig()

    frame = prepare_frame(records)
    # Splink accepts a DataFrame here; its published hints only admit table names.
    linker = Linker(frame, _splink_settings(), db_api=DuckDBAPI())  # type: ignore[arg-type]

    linker.training.estimate_probability_two_random_records_match(
        [block_on("email"), block_on("phone", "last_name_f")], recall=0.8
    )
    linker.training.estimate_u_using_random_sampling(
        max_pairs=config.em_max_pairs, seed=config.seed
    )
    linker.training.estimate_parameters_using_expectation_maximisation(block_on("email"))
    linker.training.estimate_parameters_using_expectation_maximisation(
        block_on("first_name_c", "last_name_f")
    )

    predictions = linker.inference.predict(
        threshold_match_probability=config.review_threshold
    ).as_pandas_dataframe()

    edges: list[ScoredEdge] = []
    review: list[ScoredEdge] = []
    for row in predictions.itertuples():
        edge = ScoredEdge(
            ref_l=str(row.unique_id_l),
            ref_r=str(row.unique_id_r),
            probability=float(row.match_probability),
        )
        if edge.probability >= config.auto_merge_threshold:
            edges.append(edge)
        else:
            review.append(edge)
    edges.sort(key=lambda e: (e.ref_l, e.ref_r))
    review.sort(key=lambda e: (-e.probability, e.ref_l, e.ref_r))
    return ProbabilisticResult(edges=edges, review_band=review)


@dataclass
class CombinedClusters:
    clusters: dict[str, list[str]]
    method_by_ref: dict[str, str] = field(default_factory=dict)
    score_by_ref: dict[str, float] = field(default_factory=dict)


def combine(
    records: list[IdentityRecord],
    deterministic: dict[str, list[str]],
    probabilistic: ProbabilisticResult,
) -> CombinedClusters:
    """Union deterministic clusters with high-confidence probabilistic edges.

    Method labeling: a record linked by a deterministic rule keeps
    'deterministic' even if Splink also linked it; 'probabilistic' marks
    records that only probabilistic edges pulled into their cluster.
    """
    from fanuni.unification.deterministic import UnionFind

    uf = UnionFind()
    deterministic_multi: set[str] = set()
    for members in deterministic.values():
        for ref in members:
            uf.find(ref)
        if len(members) > 1:
            deterministic_multi.update(members)
            anchor = members[0]
            for ref in members[1:]:
                uf.union(anchor, ref)

    score_by_ref: dict[str, float] = {}
    for edge in probabilistic.edges:
        uf.union(edge.ref_l, edge.ref_r)
        for ref in (edge.ref_l, edge.ref_r):
            score_by_ref[ref] = max(score_by_ref.get(ref, 0.0), edge.probability)

    clusters = uf.clusters()
    method_by_ref: dict[str, str] = {}
    for members in clusters.values():
        for ref in members:
            if ref in deterministic_multi:
                method_by_ref[ref] = "deterministic"
            elif len(members) > 1 and ref in score_by_ref:
                method_by_ref[ref] = "probabilistic"
            elif len(members) > 1:
                method_by_ref[ref] = "deterministic"
            else:
                method_by_ref[ref] = "singleton"
    return CombinedClusters(
        clusters=clusters, method_by_ref=method_by_ref, score_by_ref=score_by_ref
    )
