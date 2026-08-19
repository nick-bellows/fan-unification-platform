"""Ground-truth entity model and generator configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class GenConfig:
    seed: int = 42
    fans: int = 5000
    out_dir: str = "data"
    # The activity window all timestamps fall inside.
    window_start: date = date(2024, 8, 1)
    window_end: date = date(2026, 8, 1)
    # The month (inclusive) from which the merch export schema drifts:
    # billing_zip -> billing_postal_code, plus a new discount_code column.
    merch_drift_from: date = date(2026, 2, 1)


@dataclass(frozen=True)
class EmailPeriod:
    address: str
    valid_from: date


@dataclass(frozen=True)
class TrueFan:
    entity_id: str  # F00001 ...
    first_name: str
    last_name: str
    nickname: str | None
    emails: tuple[EmailPeriod, ...]  # ordered by valid_from ascending
    phone_digits: str  # 10 digits, no formatting
    dob: date
    city: str
    state: str
    zip_code: str
    household_id: str | None
    household_email: str | None
    fan_since: date
    # Which systems this fan appears in.
    in_crm: bool = False
    in_ticketing: bool = False
    in_merch: bool = False
    in_email: bool = False

    def email_at(self, on: date) -> str:
        """The address in force on a date (first address for earlier dates)."""
        active = self.emails[0].address
        for period in self.emails:
            if period.valid_from <= on:
                active = period.address
        return active

    @property
    def current_email(self) -> str:
        return self.emails[-1].address


@dataclass
class TruthRecord:
    """One row of the ground-truth record map: a source record -> true entity."""

    source_system: str
    source_record_id: str
    entity_id: str
    mess_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Fixture:
    match_id: str
    kickoff_at: datetime
    home_team: str
    away_team: str
    venue: str
    city: str
    competition: str
