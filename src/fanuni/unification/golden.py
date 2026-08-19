"""Golden-record survivorship and the identity-table writer.

fan_id derives from the smallest member ref of a cluster, so a stable cluster
keeps its fan_id across runs — which is what lets core.dim_fan carry real
SCD2 history.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

import psycopg

from fanuni.unification.records import IdentityRecord, fold


@dataclass(frozen=True)
class XrefRow:
    source_system: str
    source_record_id: str
    fan_id: str
    method: str  # deterministic | probabilistic | singleton
    score: float | None


@dataclass(frozen=True)
class GoldenFan:
    fan_id: str
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    dob: date | None
    sources: str
    record_count: int


def fan_id_for(members: list[str]) -> str:
    return "FAN-" + hashlib.sha1(min(members).encode()).hexdigest()[:12]


def _mode_longest(values: list[str]) -> str | None:
    """Most frequent value (folded comparison); ties break to the longest
    then lexicographic, so 'William' beats 'WILLIAM' beats a typo'd variant
    only when the typo is genuinely more common."""
    cleaned = [v for v in values if v]
    if not cleaned:
        return None
    counts = Counter(fold(v) for v in cleaned)
    best_folded, _ = max(counts.items(), key=lambda kv: (kv[1], kv[0] or ""))
    candidates = [v for v in cleaned if fold(v) == best_folded]
    return max(candidates, key=lambda v: (len(v), v))


def build_golden(cluster_members: list[IdentityRecord]) -> GoldenFan:
    members = sorted(cluster_members, key=lambda r: r.ref)
    fan_id = fan_id_for([r.ref for r in members])
    # Latest observed email wins (people move to their newest address);
    # names/locations take the modal value; DOB prefers CRM (the only
    # full-date source).
    with_email = [r for r in members if r.email]
    email = max(with_email, key=lambda r: r.observed_at).email if with_email else None
    dob = next((r.dob for r in members if r.dob), None)
    return GoldenFan(
        fan_id=fan_id,
        first_name=_mode_longest([r.first_name for r in members if r.first_name]),
        last_name=_mode_longest([r.last_name for r in members if r.last_name]),
        email=email,
        phone=_mode_longest([r.phone for r in members if r.phone]),
        city=_mode_longest([r.city for r in members if r.city]),
        state=_mode_longest([r.state for r in members if r.state]),
        zip_code=_mode_longest([r.zip_code for r in members if r.zip_code]),
        dob=dob,
        sources=",".join(sorted({r.source_system for r in members})),
        record_count=len(members),
    )


def write_identity_tables(
    conn: psycopg.Connection[Any], xref: list[XrefRow], golden: list[GoldenFan]
) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE identity.fan_xref")
        with cur.copy(
            "COPY identity.fan_xref (source_system, source_record_id, fan_id, method, score)"
            " FROM STDIN"
        ) as copy:
            for row in xref:
                copy.write_row(
                    (row.source_system, row.source_record_id, row.fan_id, row.method, row.score)
                )
        cur.execute("TRUNCATE identity.golden_fans")
        with cur.copy(
            "COPY identity.golden_fans (fan_id, first_name, last_name, email, phone,"
            " city, state, zip, dob, sources, record_count) FROM STDIN"
        ) as copy:
            for fan in golden:
                copy.write_row(
                    (
                        fan.fan_id,
                        fan.first_name,
                        fan.last_name,
                        fan.email,
                        fan.phone,
                        fan.city,
                        fan.state,
                        fan.zip_code,
                        fan.dob,
                        fan.sources,
                        fan.record_count,
                    )
                )
    conn.commit()
