"""The eval harness: score unification against generator ground truth.

Pairwise metrics over matched pairs (the record-linkage standard): a true pair
is two records of the same generated entity; a predicted pair is two records
in one cluster. Precision = TP/(TP+FP) over predicted pairs, recall over true
pairs, broken down by injected mess tag so each failure mode is visible.

This module is the only code allowed to read data/truth/. It compares the
deterministic-only baseline against deterministic+Splink head-to-head and
publishes whichever result the numbers actually show.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import psycopg

from fanuni.unification.deterministic import deterministic_clusters
from fanuni.unification.probabilistic import (
    UNIFIER_VERSION,
    CombinedClusters,
    UnifyConfig,
    combine,
    probabilistic_edges,
)
from fanuni.unification.records import IdentityRecord, fetch_identity_records

Pair = tuple[str, str]


@dataclass(frozen=True)
class PairMetrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    predicted_clusters: int
    true_entities: int


def load_truth(path: Path) -> dict[str, tuple[str, list[str]]]:
    """ref -> (entity_id, mess_tags)"""
    truth: dict[str, tuple[str, list[str]]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            ref = f"{row['source_system']}:{row['source_record_id']}"
            tags = [t for t in row["mess_tags"].split("|") if t]
            truth[ref] = (row["entity_id"], tags)
    return truth


def _pairs(groups: dict[str, list[str]]) -> set[Pair]:
    pairs: set[Pair] = set()
    for members in groups.values():
        for a, b in combinations(sorted(members), 2):
            pairs.add((a, b))
    return pairs


def pair_metrics(
    clusters: dict[str, list[str]], truth: dict[str, tuple[str, list[str]]]
) -> tuple[PairMetrics, set[Pair], set[Pair]]:
    """Metrics restricted to refs both sides know about."""
    known = {ref for members in clusters.values() for ref in members} & set(truth)
    pred = {(a, b) for a, b in _pairs(clusters) if a in known and b in known}

    by_entity: dict[str, list[str]] = {}
    for ref in known:
        by_entity.setdefault(truth[ref][0], []).append(ref)
    true = _pairs(by_entity)

    tp = len(pred & true)
    fp_pairs = pred - true
    fn_pairs = true - pred
    precision = tp / len(pred) if pred else 1.0
    recall = tp / len(true) if true else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return (
        PairMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            tp=tp,
            fp=len(fp_pairs),
            fn=len(fn_pairs),
            predicted_clusters=len(clusters),
            true_entities=len(by_entity),
        ),
        fp_pairs,
        fn_pairs,
    )


def tag_breakdown(
    truth: dict[str, tuple[str, list[str]]],
    clusters: dict[str, list[str]],
    fp_pairs: set[Pair],
    fn_pairs: set[Pair],
) -> list[dict[str, Any]]:
    """Recall per mess tag: over true pairs where at least one side carries
    the tag. FP pairs attribute to every tag either side carries."""
    known = {ref for members in clusters.values() for ref in members} & set(truth)
    by_entity: dict[str, list[str]] = {}
    for ref in known:
        by_entity.setdefault(truth[ref][0], []).append(ref)
    true_pairs = _pairs(by_entity)

    tags = sorted({t for _, (_e, ts) in truth.items() for t in ts})
    rows: list[dict[str, Any]] = []
    for tag in tags:
        tagged = {ref for ref in known if tag in truth[ref][1]}
        tag_true = {(a, b) for a, b in true_pairs if a in tagged or b in tagged}
        tag_fn = {(a, b) for a, b in fn_pairs if a in tagged or b in tagged}
        tag_fp = sum(1 for a, b in fp_pairs if a in tagged or b in tagged)
        recall = (len(tag_true) - len(tag_fn)) / len(tag_true) if tag_true else None
        rows.append(
            {
                "tag": tag,
                "true_pairs": len(tag_true),
                "pair_recall": round(recall, 4) if recall is not None else None,
                "fp_pairs": tag_fp,
            }
        )
    return rows


def _write_review_csv(
    path: Path, records: list[IdentityRecord], combined: CombinedClusters, review: list[Any]
) -> None:
    by_ref = {r.ref: r for r in records}
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["probability"]
    for side in ("l", "r"):
        columns += [f"{side}_{c}" for c in ("ref", "first", "last", "email", "phone", "zip")]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for edge in review:
            row: list[Any] = [round(edge.probability, 4)]
            for ref in (edge.ref_l, edge.ref_r):
                r = by_ref.get(ref)
                row += (
                    [ref, r.first_name, r.last_name, r.email, r.phone, r.zip_code]
                    if r
                    else [ref, "", "", "", "", ""]
                )
            writer.writerow(row)


def run_eval(
    conn: psycopg.Connection[Any],
    truth_path: Path,
    out_dir: Path,
    review_dir: Path,
    config: UnifyConfig | None = None,
) -> dict[str, Any]:
    config = config or UnifyConfig()
    records = fetch_identity_records(conn)
    truth = load_truth(truth_path)

    det_clusters = deterministic_clusters(records)
    det_metrics, det_fp, det_fn = pair_metrics(det_clusters, truth)

    prob = probabilistic_edges(records, config)
    combined = combine(records, det_clusters, prob)
    full_metrics, full_fp, full_fn = pair_metrics(combined.clusters, truth)

    det_tags = tag_breakdown(truth, det_clusters, det_fp, det_fn)
    full_tags = tag_breakdown(truth, combined.clusters, full_fp, full_fn)

    _write_review_csv(review_dir / "review_pairs.csv", records, combined, prob.review_band)

    evaluated_at = datetime.now(UTC).isoformat()
    report: dict[str, Any] = {
        "unifier_version": UNIFIER_VERSION,
        "evaluated_at": evaluated_at,
        "config": {
            "auto_merge_threshold": config.auto_merge_threshold,
            "review_threshold": config.review_threshold,
            "em_max_pairs": config.em_max_pairs,
            "seed": config.seed,
        },
        "records_evaluated": len(records),
        "review_band": len(prob.review_band),
        "variants": {
            "deterministic": {"metrics": det_metrics.__dict__, "by_tag": det_tags},
            "full": {"metrics": full_metrics.__dict__, "by_tag": full_tags},
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "linkage_eval.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "linkage_eval.md").write_text(_render_markdown(report), encoding="utf-8")

    for variant, metrics, tags in (
        ("deterministic", det_metrics, det_tags),
        ("full", full_metrics, full_tags),
    ):
        conn.execute(
            """
            INSERT INTO ops.linkage_eval
              (unifier_version, variant, pair_precision, pair_recall, pair_f1,
               tp, fp, fn, predicted_clusters, true_entities, review_band)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                UNIFIER_VERSION,
                variant,
                metrics.precision,
                metrics.recall,
                metrics.f1,
                metrics.tp,
                metrics.fp,
                metrics.fn,
                metrics.predicted_clusters,
                metrics.true_entities,
                len(prob.review_band),
            ),
        )
        for row in tags:
            conn.execute(
                """
                INSERT INTO ops.linkage_eval_tags
                  (unifier_version, variant, tag, true_pairs, pair_recall, fp_pairs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    UNIFIER_VERSION,
                    variant,
                    row["tag"],
                    row["true_pairs"],
                    row["pair_recall"],
                    row["fp_pairs"],
                ),
            )
    conn.commit()
    return report


def run_threshold_sweep(
    conn: psycopg.Connection[Any],
    truth_path: Path,
    out_dir: Path,
    thresholds: tuple[float, ...] = (0.90, 0.95, 0.99, 0.999, 0.9999),
    config: UnifyConfig | None = None,
) -> list[dict[str, Any]]:
    """Metrics at several auto-merge thresholds: how the operating point is
    chosen. One Splink pass scores everything >= 0.5; each threshold then
    slices the same predictions, so rows are directly comparable."""
    from fanuni.unification.probabilistic import ProbabilisticResult

    config = config or UnifyConfig()
    records = fetch_identity_records(conn)
    truth = load_truth(truth_path)

    det = deterministic_clusters(records)
    det_metrics, _, _ = pair_metrics(det, truth)
    rows: list[dict[str, Any]] = [
        {
            "variant": "deterministic",
            "threshold": None,
            "precision": det_metrics.precision,
            "recall": det_metrics.recall,
            "f1": det_metrics.f1,
            "auto_merge_edges": 0,
            "review_band": 0,
        }
    ]

    base_config = UnifyConfig(
        auto_merge_threshold=0.5,
        review_threshold=0.5,
        em_max_pairs=config.em_max_pairs,
        seed=config.seed,
    )
    scored = probabilistic_edges(records, base_config).edges
    for threshold in thresholds:
        kept = [e for e in scored if e.probability >= threshold]
        combined = combine(records, det, ProbabilisticResult(edges=kept, review_band=[]))
        metrics, _, _ = pair_metrics(combined.clusters, truth)
        rows.append(
            {
                "variant": "full",
                "threshold": threshold,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "auto_merge_edges": len(kept),
                "review_band": sum(1 for e in scored if 0.5 <= e.probability < threshold),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Auto-merge threshold sweep",
        "",
        f"- Unifier version: {UNIFIER_VERSION} · seed {config.seed} · {len(records)} records",
        "- One Splink pass scored every pair >= 0.5; each row slices the same",
        "  predictions at a different auto-merge threshold, against ground truth.",
        "",
        "| variant | threshold | precision | recall | F1 | merged edges | pairs below |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        threshold_label = "—" if row["threshold"] is None else f"{row['threshold']}"
        lines.append(
            f"| {row['variant']} | {threshold_label} | {row['precision']:.4f}"
            f" | {row['recall']:.4f} | {row['f1']:.4f}"
            f" | {row['auto_merge_edges']} | {row['review_band']} |"
        )
    lines += [
        "",
        "With many agreeing fields the Fellegi-Sunter posterior saturates near",
        "1.0, so most false positives (households sharing email/surname/zip and",
        "name+geography coincidences) still score above 0.999 — the useful",
        "separation happens in the last decimal places. The default operating",
        "point (`UnifyConfig.auto_merge_threshold`) was chosen from this table;",
        "changing it means bumping UNIFIER_VERSION and regenerating this file",
        "in the same commit.",
        "",
    ]
    (out_dir / "threshold_sweep.md").write_text("\n".join(lines), encoding="utf-8")
    return rows


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Linkage evaluation",
        "",
        f"- Unifier version: {report['unifier_version']}",
        f"- Evaluated: {report['evaluated_at']}",
        f"- Records: {report['records_evaluated']} · Review band: {report['review_band']} pairs",
        f"- Config: {json.dumps(report['config'])}",
        "",
        "| variant | precision | recall | F1 | TP | FP | FN | clusters | true entities |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for variant, data in report["variants"].items():
        m = data["metrics"]
        lines.append(
            f"| {variant} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f}"
            f" | {m['tp']} | {m['fp']} | {m['fn']}"
            f" | {m['predicted_clusters']} | {m['true_entities']} |"
        )
    lines += ["", "## Recall by mess tag", ""]
    lines.append("| tag | true pairs | det recall | full recall | det FP | full FP |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    det_by_tag = {r["tag"]: r for r in report["variants"]["deterministic"]["by_tag"]}
    for row in report["variants"]["full"]["by_tag"]:
        det_row = det_by_tag.get(row["tag"], {})

        def fmt(value: Any) -> str:
            return f"{value:.4f}" if isinstance(value, float) else "—"

        lines.append(
            f"| {row['tag']} | {row['true_pairs']} | {fmt(det_row.get('pair_recall'))}"
            f" | {fmt(row['pair_recall'])} | {det_row.get('fp_pairs', 0)}"
            f" | {row['fp_pairs']} |"
        )
    lines.append("")
    return "\n".join(lines)
