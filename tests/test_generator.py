import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from fanuni.generator.model import GenConfig
from fanuni.generator.run import generate, tree_digest


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_same_seed_same_bytes(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    generate(GenConfig(seed=11, fans=100, out_dir=str(a)))
    generate(GenConfig(seed=11, fans=100, out_dir=str(b)))
    assert tree_digest(a) == tree_digest(b)


def test_regeneration_clears_stale_outputs(tmp_path: Path) -> None:
    out = tmp_path / "data"
    stale = out / "dropzone" / "ticketing" / "orders_1999-01.jsonl"
    stale.parent.mkdir(parents=True)
    stale.write_text('{"stale": true}\n', encoding="utf-8")
    generate(GenConfig(seed=11, fans=60, out_dir=str(out)))
    assert not stale.exists()


def test_different_seed_different_bytes(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    generate(GenConfig(seed=11, fans=100, out_dir=str(a)))
    generate(GenConfig(seed=12, fans=100, out_dir=str(b)))
    assert tree_digest(a) != tree_digest(b)


def test_truth_map_covers_every_identity_record(small_dataset: tuple[Path, dict]) -> None:
    out, manifest = small_dataset
    truth = _read_csv(out / "truth" / "record_map.csv")
    by_source: Counter[str] = Counter(t["source_system"] for t in truth)

    contacts = _read_jsonl(out / "sfmock" / "contacts.jsonl")
    assert by_source["crm"] == len(contacts)
    assert {t["source_record_id"] for t in truth if t["source_system"] == "crm"} == {
        c["Id"] for c in contacts
    }

    ticket_ids = {
        row["order_id"]
        for path in (out / "dropzone" / "ticketing").glob("orders_*.jsonl")
        for row in _read_jsonl(path)
    }
    assert by_source["ticketing"] == len(ticket_ids)

    merch_orders = {
        row["order_number"]
        for path in (out / "dropzone" / "merch").glob("orders_*.csv")
        for row in _read_csv(path)
    }
    assert by_source["merch"] == len(merch_orders)

    subscriber_ids = {
        row["subscriber_id"]
        for path in (out / "dropzone" / "email").glob("subscribers_*.csv")
        for row in _read_csv(path)
    }
    assert by_source["email"] == len(subscriber_ids)

    # Every truth entity exists in entities.jsonl.
    entities = {e["entity_id"] for e in _read_jsonl(out / "truth" / "entities.jsonl")}
    assert {t["entity_id"] for t in truth} <= entities
    assert manifest["counts"]["truth_records"] == len(truth)


@pytest.mark.parametrize(
    "tag",
    [
        "nickname",
        "typo",
        "case",
        "stale_email",
        "shared_email",
        "within_source_dup",
        "resubscribed_new_email",
        "name_format",
        "diacritics",
        "missing_dob",
        "late_arrival",
    ],
)
def test_mess_taxonomy_all_present(small_dataset: tuple[Path, dict], tag: str) -> None:
    _, manifest = small_dataset
    assert manifest["mess_tag_counts"].get(tag, 0) > 0, f"mess type {tag} never generated"


def test_merch_schema_drift(small_dataset: tuple[Path, dict]) -> None:
    out, manifest = small_dataset
    drift = manifest["merch_drift_from"][:7]
    pre = post = 0
    for path in sorted((out / "dropzone" / "merch").glob("orders_*.csv")):
        header = path.read_text(encoding="utf-8").splitlines()[0]
        batch = path.stem.removeprefix("orders_")
        if batch >= drift:
            assert "billing_postal_code" in header and "discount_code" in header
            post += 1
        else:
            assert "billing_zip" in header and "discount_code" not in header
            pre += 1
    assert pre > 0 and post > 0


def test_data_is_visibly_synthetic(small_dataset: tuple[Path, dict]) -> None:
    out, manifest = small_dataset
    assert "SYNTHETIC" in manifest["note"]
    contacts = _read_jsonl(out / "sfmock" / "contacts.jsonl")
    assert all(
        c["Email"].partition("@")[2].endswith(("example.com", "example.net", "example.org"))
        for c in contacts
    )
