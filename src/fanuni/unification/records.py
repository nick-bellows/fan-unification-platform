"""Load identity records from the warehouse."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import psycopg


@dataclass(frozen=True)
class IdentityRecord:
    source_system: str
    source_record_id: str
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    dob: date | None
    birth_year: int | None
    observed_at: datetime

    @property
    def ref(self) -> str:
        return f"{self.source_system}:{self.source_record_id}"


def fold(value: str | None) -> str | None:
    """Casefold + strip diacritics: the match-key normalization for names."""
    if not value:
        return None
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return folded.lower().strip() or None


def fetch_identity_records(conn: psycopg.Connection[Any]) -> list[IdentityRecord]:
    rows = conn.execute(
        """
        SELECT source_system, source_record_id, first_name, last_name, email,
               phone, city, state, zip, dob, birth_year, observed_at
        FROM staging.identity_records
        ORDER BY source_system, source_record_id
        """
    ).fetchall()
    return [
        IdentityRecord(
            source_system=r[0],
            source_record_id=r[1],
            first_name=r[2],
            last_name=r[3],
            email=r[4] or None,
            phone=r[5] or None,
            city=r[6] or None,
            state=r[7] or None,
            zip_code=r[8] or None,
            dob=r[9],
            birth_year=r[10],
            observed_at=r[11],
        )
        for r in rows
    ]
