"""Generate all source files, the ground truth, and the manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fanuni import __version__
from fanuni.generator.model import GenConfig, TruthRecord
from fanuni.generator.population import build_population
from fanuni.generator.sources import (
    emit_crm,
    emit_email,
    emit_fixtures,
    emit_merch,
    emit_ticketing,
    month_key,
)

MERCH_COLUMNS_PRE_DRIFT = [
    "order_number",
    "created_at",
    "customer_email",
    "billing_name",
    "billing_zip",
    "sku",
    "item_name",
    "quantity",
    "unit_price",
    "line_total",
]
MERCH_COLUMNS_POST_DRIFT = [
    "order_number",
    "created_at",
    "customer_email",
    "billing_name",
    "billing_postal_code",
    "sku",
    "item_name",
    "quantity",
    "unit_price",
    "line_total",
    "discount_code",
]

SUBSCRIBER_COLUMNS = [
    "subscriber_id",
    "email",
    "first_name",
    "last_name",
    "signup_date",
    "status",
    "birth_year",
    "zip",
]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: ("" if row.get(c) is None else row.get(c)) for c in columns})


def generate(config: GenConfig) -> dict[str, Any]:
    """Run the full generation; returns the manifest that was written."""
    out = Path(config.out_dir)
    # The generator owns its output dirs: clear them first, or a smaller
    # regeneration leaves stale files from a larger earlier run in months the
    # new run doesn't write (a real bug the integration suite caught). Clear
    # CONTENTS rather than the dirs themselves — data/sfmock is bind-mounted
    # into the mock-Salesforce container, and on Linux removing a mounted
    # dir's source detaches the mount, leaving the mock serving nothing.
    for sub in ("dropzone", "sfmock", "truth"):
        target = out / sub
        if not target.is_dir():
            continue
        for child in target.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
    fans = build_population(config)
    # A separate, deterministically derived stream for emission keeps
    # population and record-level randomness independent but reproducible.
    rng = random.Random(config.seed + 1_000_003)

    fixtures = emit_fixtures(config, rng)
    contacts, opportunities, crm_truth = emit_crm(config, rng, fans)
    ticket_batches, ticket_truth = emit_ticketing(config, rng, fans, fixtures)
    merch_batches, merch_truth = emit_merch(config, rng, fans)
    sub_batches, event_batches, campaigns, email_truth = emit_email(config, rng, fans)

    # --- source systems ---
    _write_jsonl(out / "sfmock" / "contacts.jsonl", contacts)
    _write_jsonl(out / "sfmock" / "opportunities.jsonl", opportunities)

    for batch, rows in sorted(ticket_batches.items()):
        _write_jsonl(out / "dropzone" / "ticketing" / f"orders_{batch}.jsonl", rows)

    drift_month = month_key(config.merch_drift_from)
    for batch, rows in sorted(merch_batches.items()):
        columns = MERCH_COLUMNS_POST_DRIFT if batch >= drift_month else MERCH_COLUMNS_PRE_DRIFT
        _write_csv(out / "dropzone" / "merch" / f"orders_{batch}.csv", rows, columns)

    for batch, rows in sorted(sub_batches.items()):
        _write_csv(
            out / "dropzone" / "email" / f"subscribers_{batch}.csv", rows, SUBSCRIBER_COLUMNS
        )
    for batch, rows in sorted(event_batches.items()):
        _write_jsonl(out / "dropzone" / "email" / f"events_{batch}.jsonl", rows)
    _write_csv(
        out / "dropzone" / "email" / "campaigns.csv",
        campaigns,
        ["campaign_id", "name", "sent_at"],
    )

    _write_csv(
        out / "dropzone" / "fixtures" / "fixtures.csv",
        [
            {
                "match_id": f.match_id,
                "kickoff_at": f.kickoff_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "home_team": f.home_team,
                "away_team": f.away_team,
                "venue": f.venue,
                "city": f.city,
                "competition": f.competition,
            }
            for f in fixtures
        ],
        ["match_id", "kickoff_at", "home_team", "away_team", "venue", "city", "competition"],
    )

    # --- ground truth (never read by the pipeline; only by the eval harness) ---
    truth: list[TruthRecord] = crm_truth + ticket_truth + merch_truth + email_truth
    _write_jsonl(
        out / "truth" / "entities.jsonl",
        [
            {
                **asdict(fan),
                "dob": fan.dob.isoformat(),
                "fan_since": fan.fan_since.isoformat(),
                "emails": [
                    {"address": p.address, "valid_from": p.valid_from.isoformat()}
                    for p in fan.emails
                ],
            }
            for fan in fans
        ],
    )
    _write_csv(
        out / "truth" / "record_map.csv",
        [
            {
                "source_system": t.source_system,
                "source_record_id": t.source_record_id,
                "entity_id": t.entity_id,
                "mess_tags": "|".join(t.mess_tags),
            }
            for t in truth
        ],
        ["source_system", "source_record_id", "entity_id", "mess_tags"],
    )

    tag_counts = Counter(tag for t in truth for tag in t.mess_tags)
    manifest: dict[str, Any] = {
        "generator_version": __version__,
        "seed": config.seed,
        "fans": config.fans,
        "window": [config.window_start.isoformat(), config.window_end.isoformat()],
        "merch_drift_from": config.merch_drift_from.isoformat(),
        "note": "ALL DATA IS SYNTHETIC. Generated by fanuni.generator; no real persons.",
        "counts": {
            "entities": len(fans),
            "households": len({f.household_id for f in fans if f.household_id}),
            "fixtures": len(fixtures),
            "crm_contacts": len(contacts),
            "crm_opportunities": len(opportunities),
            "ticket_orders": sum(len(r) for r in ticket_batches.values()),
            "merch_line_rows": sum(len(r) for r in merch_batches.values()),
            "merch_orders": len(merch_truth),
            "email_subscribers": len(email_truth),
            "email_events": sum(len(r) for r in event_batches.values()),
            "campaigns": len(campaigns),
            "truth_records": len(truth),
        },
        "mess_tag_counts": dict(sorted(tag_counts.items())),
    }
    (out / "truth").mkdir(parents=True, exist_ok=True)
    (out / "truth" / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def tree_digest(root: Path) -> str:
    """SHA256 over every file's relative path and content — determinism checks."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).replace("\\", "/").encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
