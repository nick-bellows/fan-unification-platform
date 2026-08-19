"""Identity-mess corruption functions.

Each function is pure given the RNG; the caller records which corruptions were
applied as tags in the ground-truth record map, so unification accuracy can be
broken down by mess type.
"""

from __future__ import annotations

import random
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from fanuni.generator.model import TrueFan


def typo(rng: random.Random, s: str) -> str:
    """One character-level edit: substitute, transpose, or delete."""
    if len(s) < 4:
        return s
    pos = rng.randrange(1, len(s) - 1)
    op = rng.randrange(3)
    if op == 0:
        return s[:pos] + rng.choice("abcdefghijklmnopqrstuvwxyz") + s[pos + 1 :]
    if op == 1:
        return s[:pos] + s[pos + 1] + s[pos] + s[pos + 2 :]
    return s[:pos] + s[pos + 1 :]


def vary_case(rng: random.Random, s: str) -> str:
    return s.upper() if rng.random() < 0.5 else s.lower()


def strip_diacritics(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


PHONE_STYLES = ("{a}{b}{c}", "({a}) {b}-{c}", "{a}-{b}-{c}", "{a}.{b}.{c}", "+1{a}{b}{c}")


def format_phone(rng: random.Random, digits: str) -> str:
    a, b, c = digits[:3], digits[3:6], digits[6:]
    return rng.choice(PHONE_STYLES).format(a=a, b=b, c=c)


@dataclass
class PersonView:
    """How one source record sees a fan, after corruption."""

    first_name: str
    last_name: str
    email: str
    phone: str
    zip_code: str
    dob: date | None
    tags: list[str] = field(default_factory=list)


def person_view(
    rng: random.Random,
    fan: TrueFan,
    on: date,
    *,
    allow_household_email: bool = False,
    include_dob: bool = False,
) -> PersonView:
    """Project a fan into a source record's fields, applying tagged mess."""
    tags: list[str] = []

    email = fan.email_at(on)
    if email != fan.current_email:
        tags.append("stale_email")
    if allow_household_email and fan.household_email and rng.random() < 0.30:
        email = fan.household_email
        tags.append("shared_email")

    first, last = fan.first_name, fan.last_name
    if fan.nickname and rng.random() < 0.25:
        first = fan.nickname
        tags.append("nickname")

    if (first + last) != strip_diacritics(first + last) and rng.random() < 0.50:
        first, last = strip_diacritics(first), strip_diacritics(last)
        tags.append("diacritics")

    if rng.random() < 0.06:
        if rng.random() < 0.5:
            last = typo(rng, last)
        else:
            local, _, domain = email.partition("@")
            email = f"{typo(rng, local)}@{domain}"
        tags.append("typo")

    if rng.random() < 0.08:
        first, last = vary_case(rng, first), vary_case(rng, last)
        tags.append("case")

    dob: date | None = None
    if include_dob and rng.random() >= 0.15:
        dob = fan.dob
    elif include_dob:
        tags.append("missing_dob")

    return PersonView(
        first_name=first,
        last_name=last,
        email=email,
        phone=format_phone(rng, fan.phone_digits),
        zip_code=fan.zip_code,
        dob=dob,
        tags=tags,
    )
