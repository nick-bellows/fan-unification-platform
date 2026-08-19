"""Build the true fan population: the entities every source record derives from."""

from __future__ import annotations

import random
import unicodedata
from datetime import date, timedelta

from faker import Faker

from fanuni.generator.model import EmailPeriod, GenConfig, TrueFan
from fanuni.generator.names import ACCENTED_NAMES, NICKNAMES

EMAIL_DOMAINS = (
    "example.com",
    "example.net",
    "example.org",
    "mail.example.com",
    "inbox.example.net",
)

_AREA_CODES = ("404", "470", "678", "770", "214", "469", "972", "312", "773", "206", "303")


def ascii_fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _phone_digits(rng: random.Random) -> str:
    return rng.choice(_AREA_CODES) + f"{rng.randint(2000000, 9999999):07d}"


def _email_for(rng: random.Random, first: str, last: str, suffix: str = "") -> str:
    first_a, last_a = ascii_fold(first), ascii_fold(last)
    style = rng.randrange(4)
    local = (
        f"{first_a}.{last_a}"
        if style == 0
        else f"{first_a[0]}{last_a}"
        if style == 1
        else f"{first_a}{rng.randint(1, 99)}"
        if style == 2
        else f"{last_a}.{first_a[0]}"
    )
    return f"{local}{suffix}@{rng.choice(EMAIL_DOMAINS)}"


def _random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_population(config: GenConfig) -> list[TrueFan]:
    """Deterministic for a given config: same seed, same population."""
    rng = random.Random(config.seed)
    faker = Faker("en_US")
    faker.seed_instance(config.seed)

    fans: list[TrueFan] = []
    formal_names = sorted(NICKNAMES)
    n = config.fans
    i = 0
    household_seq = 0

    while len(fans) < n:
        # Either a household (2-3 members sharing surname/address/household
        # email — a classic identity-resolution trap) or a single fan.
        make_household = rng.random() < 0.10 and len(fans) + 2 <= n
        size = rng.randint(2, 3) if make_household else 1

        household_id: str | None = None
        household_email: str | None = None
        shared_last: str | None = None
        shared_addr: tuple[str, str, str] | None = None
        if make_household:
            household_seq += 1
            household_id = f"H{household_seq:05d}"

        for _ in range(size):
            i += 1
            roll = rng.random()
            if roll < 0.06:
                first, last = rng.choice(ACCENTED_NAMES)
            elif roll < 0.50:
                first = rng.choice(formal_names)
                last = faker.last_name()
            else:
                first = faker.first_name()
                last = faker.last_name()
            if shared_last is not None:
                last = shared_last
            elif make_household:
                shared_last = last

            if shared_addr is not None:
                city, state, zip_code = shared_addr
            else:
                city, state, zip_code = faker.city(), faker.state_abbr(), faker.zipcode()
                if make_household:
                    shared_addr = (city, state, zip_code)

            fan_since_floor = config.window_start - timedelta(days=365 * 4)
            fan_since = _random_date(rng, fan_since_floor, config.window_end)

            emails = [EmailPeriod(_email_for(rng, first, last), date(1990, 1, 1))]
            # ~10% change their email partway through the window.
            if rng.random() < 0.10:
                change_on = _random_date(
                    rng,
                    config.window_start + timedelta(days=90),
                    config.window_end - timedelta(days=90),
                )
                new_addr = _email_for(rng, first, last, str(rng.randint(1, 9)))
                emails.append(EmailPeriod(new_addr, change_on))

            if make_household and household_email is None:
                household_email = f"the.{ascii_fold(last)}.family@{rng.choice(EMAIL_DOMAINS)}"

            nickname = rng.choice(NICKNAMES[first]) if first in NICKNAMES else None

            # Source membership; retry until the fan exists somewhere.
            while True:
                in_crm = rng.random() < 0.50
                in_email = rng.random() < 0.75
                in_ticketing = rng.random() < 0.55
                in_merch = rng.random() < 0.35
                if in_crm or in_email or in_ticketing or in_merch:
                    break

            fans.append(
                TrueFan(
                    entity_id=f"F{i:05d}",
                    first_name=first,
                    last_name=last,
                    nickname=nickname,
                    emails=tuple(emails),
                    phone_digits=_phone_digits(rng),
                    dob=_random_date(rng, date(1955, 1, 1), date(2012, 12, 31)),
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    household_id=household_id,
                    household_email=household_email if make_household else None,
                    fan_since=fan_since,
                    in_crm=in_crm,
                    in_ticketing=in_ticketing,
                    in_merch=in_merch,
                    in_email=in_email,
                )
            )
    return fans
