"""Project the true population into each source system's records.

Every identity-bearing record (CRM contact, ticketing order, merch order,
email subscriber) gets a TruthRecord mapping it back to its entity, tagged
with the mess applied — the eval harness scores unification against these.
"""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, time, timedelta

from fanuni.generator.mess import person_view
from fanuni.generator.model import Fixture, GenConfig, TrueFan, TruthRecord

OPPONENTS = (
    "Atlantica",
    "Borduria",
    "Caldonia",
    "Meridia",
    "Norlandia",
    "Vespugia",
    "Zephyria",
    "Aurelia",
    "Pacifica",
    "Montaria",
)

VENUES = (
    ("Riverbend Stadium", "Atlanta"),
    ("Harbor Point Park", "Seattle"),
    ("Prairie Gate Field", "Dallas"),
    ("Lakeshore Arena", "Chicago"),
    ("Canyon Ridge Stadium", "Denver"),
)

COMPETITIONS = ("International Friendly", "Continental Cup Qualifier", "Federation Cup")

SECTIONS = (("Supporters", 35.0), ("Sideline", 75.0), ("Club", 120.0), ("Suite", 250.0))

PRODUCTS = (
    ("JER-H-M", "Home Jersey (Men's)", 89.99),
    ("JER-A-M", "Away Jersey (Men's)", 89.99),
    ("JER-H-W", "Home Jersey (Women's)", 89.99),
    ("SCARF-CL", "Classic Scarf", 24.99),
    ("HOOD-CR", "Crest Hoodie", 59.99),
    ("CAP-CL", "Classic Cap", 27.99),
    ("BALL-RP", "Replica Match Ball", 34.99),
    ("POST-TM", "Team Poster", 14.99),
    ("MUG-CR", "Crest Mug", 16.99),
    ("KIT-YTH", "Youth Kit", 49.99),
)

CAMPAIGN_THEMES = (
    "Matchday Preview",
    "Kit Launch",
    "Membership Renewal",
    "Behind the Badge",
    "Ticket Presale",
    "Supporter Spotlight",
)


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _months(config: GenConfig) -> list[date]:
    months: list[date] = []
    cur = config.window_start.replace(day=1)
    while cur <= config.window_end:
        months.append(cur)
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months


def _ts(rng: random.Random, d: date) -> str:
    moment = datetime.combine(d, time(rng.randrange(8, 22), rng.randrange(60)), tzinfo=UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rand_date(rng: random.Random, start: date, end: date) -> date:
    if end < start:
        return start
    return start + timedelta(days=rng.randint(0, (end - start).days))


def emit_fixtures(config: GenConfig, rng: random.Random) -> list[Fixture]:
    fixtures: list[Fixture] = []
    months = _months(config)
    seq = 0
    for m in months:
        for squad in ("Men", "Women"):
            if rng.random() < 0.55:  # not every squad plays a home match every month
                continue
            seq += 1
            venue, city = rng.choice(VENUES)
            kickoff = datetime.combine(
                _rand_date(rng, m, min(config.window_end, m + timedelta(days=27))),
                time(19, rng.choice((0, 30))),
                tzinfo=UTC,
            )
            fixtures.append(
                Fixture(
                    match_id=f"MTCH-{seq:04d}",
                    kickoff_at=kickoff,
                    home_team=f"National XI ({squad})",
                    away_team=rng.choice(OPPONENTS),
                    venue=venue,
                    city=city,
                    competition=rng.choice(COMPETITIONS),
                )
            )
    return fixtures


def emit_crm(
    config: GenConfig, rng: random.Random, fans: list[TrueFan]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[TruthRecord]]:
    contacts: list[dict[str, object]] = []
    opportunities: list[dict[str, object]] = []
    truth: list[TruthRecord] = []
    contact_seq = 0
    opp_seq = 0

    for fan in fans:
        if not fan.in_crm:
            continue
        created = _rand_date(rng, max(fan.fan_since, config.window_start), config.window_end)
        email_changed = len(fan.emails) > 1
        change_date = fan.emails[-1].valid_from if email_changed else None
        # 60% of email-changers update their CRM contact; the update bumps
        # SystemModstamp, which is what watermark extraction keys on.
        updates_crm = email_changed and change_date is not None and rng.random() < 0.60
        view_on = config.window_end if updates_crm else created
        modstamp = (
            change_date
            if updates_crm and change_date is not None and change_date > created
            else created
        )

        n_records = 2 if rng.random() < 0.03 else 1  # duplicate-contact mess
        primary_contact_id = ""
        for dup_i in range(n_records):
            contact_seq += 1
            contact_id = f"003{contact_seq:012d}"
            if dup_i == 0:
                primary_contact_id = contact_id
            view = person_view(rng, fan, view_on, include_dob=True)
            tags = list(view.tags)
            rec_created = created if dup_i == 0 else _rand_date(rng, created, config.window_end)
            if dup_i > 0:
                tags.append("within_source_dup")
            contacts.append(
                {
                    "Id": contact_id,
                    "FirstName": view.first_name,
                    "LastName": view.last_name,
                    "Email": view.email,
                    "Phone": view.phone,
                    "MailingCity": fan.city,
                    "MailingState": fan.state,
                    "MailingPostalCode": view.zip_code,
                    "Birthdate": view.dob.isoformat() if view.dob else None,
                    "Member_Since__c": fan.fan_since.isoformat(),
                    "CreatedDate": _ts(rng, rec_created),
                    "SystemModstamp": _ts(rng, max(modstamp, rec_created)),
                }
            )
            truth.append(TruthRecord("crm", contact_id, fan.entity_id, tags))

        # Memberships: one Closed Won opportunity per window year, 70% renewal.
        for year in range(config.window_start.year, config.window_end.year + 1):
            if rng.random() >= 0.70:
                continue
            close = _rand_date(
                rng,
                max(config.window_start, date(year, 1, 1)),
                min(config.window_end, date(year, 12, 31)),
            )
            if close < max(fan.fan_since, config.window_start):
                continue
            opp_seq += 1
            opportunities.append(
                {
                    "Id": f"006{opp_seq:012d}",
                    "ContactId": primary_contact_id,
                    "Name": f"Membership {year}",
                    "Type": "Membership",
                    "StageName": "Closed Won",
                    "Amount": rng.choice((45.0, 60.0, 75.0, 90.0)),
                    "CloseDate": close.isoformat(),
                    "SystemModstamp": _ts(rng, close),
                }
            )
        if rng.random() < 0.15:  # donors
            for _ in range(rng.randint(1, 3)):
                close = _rand_date(rng, config.window_start, config.window_end)
                opp_seq += 1
                opportunities.append(
                    {
                        "Id": f"006{opp_seq:012d}",
                        "ContactId": primary_contact_id,
                        "Name": "Donation",
                        "Type": "Donation",
                        "StageName": "Closed Won",
                        "Amount": float(rng.randint(25, 500)),
                        "CloseDate": close.isoformat(),
                        "SystemModstamp": _ts(rng, close),
                    }
                )
    return contacts, opportunities, truth


def _purchaser_name(rng: random.Random, first: str, last: str, tags: list[str]) -> str:
    roll = rng.random()
    if roll < 0.75:
        return f"{first} {last}"
    tags.append("name_format")
    if roll < 0.88:
        return f"{last.upper()}, {first}"
    middle = rng.choice("ABCDEFGHJKLMRSTW")
    return f"{first} {middle}. {last}"


def emit_ticketing(
    config: GenConfig, rng: random.Random, fans: list[TrueFan], fixtures: list[Fixture]
) -> tuple[dict[str, list[dict[str, object]]], list[TruthRecord]]:
    batches: dict[str, list[dict[str, object]]] = {}
    truth: list[TruthRecord] = []
    seq = 0
    for fan in fans:
        if not fan.in_ticketing or not fixtures:
            continue
        for _ in range(rng.randint(1, 4)):
            fixture = rng.choice(fixtures)
            kickoff_day = fixture.kickoff_at.date()
            purchased = _rand_date(
                rng, max(config.window_start, kickoff_day - timedelta(days=60)), kickoff_day
            )
            view = person_view(rng, fan, purchased, allow_household_email=True)
            tags = list(view.tags)
            seq += 1
            order_id = f"T-{seq:06d}"
            section, unit_price = rng.choice(SECTIONS)
            qty = rng.randint(1, 4)
            delivered = purchased
            if rng.random() < 0.02:
                delivered = purchased + timedelta(days=rng.randint(7, 30))
                tags.append("late_arrival")
            batches.setdefault(month_key(delivered), []).append(
                {
                    "order_id": order_id,
                    "match_id": fixture.match_id,
                    "purchased_at": _ts(rng, purchased),
                    "channel": rng.choice(("web", "app", "box_office")),
                    "section": section,
                    "qty": qty,
                    "unit_price": unit_price,
                    "total": round(unit_price * qty, 2),
                    "purchaser_name": _purchaser_name(rng, view.first_name, view.last_name, tags),
                    "purchaser_email": view.email,
                    "purchaser_phone": view.phone,
                    "purchaser_zip": view.zip_code if rng.random() < 0.70 else None,
                }
            )
            truth.append(TruthRecord("ticketing", order_id, fan.entity_id, tags))
    return batches, truth


def emit_merch(
    config: GenConfig, rng: random.Random, fans: list[TrueFan]
) -> tuple[dict[str, list[dict[str, object]]], list[TruthRecord]]:
    batches: dict[str, list[dict[str, object]]] = {}
    truth: list[TruthRecord] = []
    seq = 0
    for fan in fans:
        if not fan.in_merch:
            continue
        for _ in range(rng.randint(1, 3)):
            ordered = _rand_date(rng, config.window_start, config.window_end)
            view = person_view(rng, fan, ordered, allow_household_email=True)
            tags = list(view.tags)
            seq += 1
            order_number = f"M-{seq:06d}"
            drifted = ordered >= config.merch_drift_from
            for _item in range(rng.randint(1, 2)):
                sku, item_name, price = rng.choice(PRODUCTS)
                qty = rng.randint(1, 2)
                row: dict[str, object] = {
                    "order_number": order_number,
                    "created_at": _ts(rng, ordered),
                    "customer_email": view.email,
                    "billing_name": f"{view.first_name} {view.last_name}",
                    "sku": sku,
                    "item_name": item_name,
                    "quantity": qty,
                    "unit_price": price,
                    "line_total": round(price * qty, 2),
                }
                # Schema drift (ADR'd in the plan): the export renames the zip
                # column and adds discount_code from merch_drift_from onward.
                if drifted:
                    row["billing_postal_code"] = view.zip_code
                    row["discount_code"] = (
                        rng.choice(("FAN10", "SPRING25", "KITLAUNCH"))
                        if rng.random() < 0.10
                        else ""
                    )
                else:
                    row["billing_zip"] = view.zip_code
                batches.setdefault(month_key(ordered), []).append(row)
            truth.append(TruthRecord("merch", order_number, fan.entity_id, tags))
    return batches, truth


def emit_email(
    config: GenConfig, rng: random.Random, fans: list[TrueFan]
) -> tuple[
    dict[str, list[dict[str, object]]],
    dict[str, list[dict[str, object]]],
    list[dict[str, object]],
    list[TruthRecord],
]:
    sub_batches: dict[str, list[dict[str, object]]] = {}
    event_batches: dict[str, list[dict[str, object]]] = {}
    truth: list[TruthRecord] = []
    subscribers: list[tuple[str, date, bool, str]] = []  # (id, signup, subscribed, email)
    seq = 0

    for fan in fans:
        if not fan.in_email:
            continue
        signup_floor = max(fan.fan_since, config.window_start - timedelta(days=730))
        signup = _rand_date(rng, signup_floor, config.window_end)
        records: list[tuple[date, bool]] = [(signup, False)]
        # An email change often shows up as a brand-new subscriber record —
        # a within-source duplicate the unifier must catch.
        if len(fan.emails) > 1 and rng.random() < 0.50:
            change = fan.emails[-1].valid_from
            if change > signup:
                records.append((_rand_date(rng, change, config.window_end), True))

        for rec_signup, is_resub in records:
            seq += 1
            sub_id = f"S-{seq:06d}"
            view = person_view(rng, fan, rec_signup, include_dob=False)
            tags = list(view.tags)
            if is_resub:
                view.email = fan.current_email
                tags.append("resubscribed_new_email")
            subscribed = rng.random() >= 0.10
            batch = month_key(max(rec_signup, config.window_start))
            sub_batches.setdefault(batch, []).append(
                {
                    "subscriber_id": sub_id,
                    "email": view.email,
                    "first_name": view.first_name,
                    "last_name": view.last_name,
                    "signup_date": rec_signup.isoformat(),
                    "status": "subscribed" if subscribed else "unsubscribed",
                    "birth_year": fan.dob.year if rng.random() < 0.60 else None,
                    "zip": view.zip_code if rng.random() < 0.80 else None,
                }
            )
            truth.append(TruthRecord("email", sub_id, fan.entity_id, tags))
            subscribers.append((sub_id, rec_signup, subscribed, view.email))

    campaigns: list[dict[str, object]] = []
    event_seq = 0
    for m in _months(config):
        campaign_id = f"C-{month_key(m)}"
        sent_on = _rand_date(rng, m, min(m + timedelta(days=20), config.window_end))
        campaigns.append(
            {
                "campaign_id": campaign_id,
                "name": f"{rng.choice(CAMPAIGN_THEMES)} — {month_key(m)}",
                "sent_at": _ts(rng, sent_on),
            }
        )
        for sub_id, signup, subscribed, _email in subscribers:
            if not subscribed or signup > sent_on or rng.random() >= 0.60:
                continue
            opened = rng.random() < 0.45
            clicked = opened and rng.random() < 0.25
            for event_type in (
                ("send",) + (("open",) if opened else ()) + (("click",) if clicked else ())
            ):
                event_seq += 1
                occurred = sent_on + timedelta(days=rng.randint(0, 2))
                event_batches.setdefault(month_key(occurred), []).append(
                    {
                        "event_id": f"E-{event_seq:07d}",
                        "subscriber_id": sub_id,
                        "campaign_id": campaign_id,
                        "event_type": event_type,
                        "occurred_at": _ts(rng, occurred),
                    }
                )
    return sub_batches, event_batches, campaigns, truth
