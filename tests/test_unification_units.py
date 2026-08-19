from datetime import UTC, datetime

from fanuni.unification.deterministic import UnionFind, deterministic_clusters
from fanuni.unification.golden import _mode_longest, build_golden, fan_id_for
from fanuni.unification.records import IdentityRecord, fold


def _record(
    ref: str,
    email: str | None = None,
    phone: str | None = None,
    last: str | None = "Example",
    first: str | None = "Sam",
    observed: datetime | None = None,
) -> IdentityRecord:
    source, _, record_id = ref.partition(":")
    return IdentityRecord(
        source_system=source,
        source_record_id=record_id,
        first_name=first,
        last_name=last,
        email=email,
        phone=phone,
        city=None,
        state=None,
        zip_code="30303",
        dob=None,
        birth_year=None,
        observed_at=observed or datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_union_find_is_transitive_with_stable_roots() -> None:
    uf = UnionFind()
    uf.union("b", "c")
    uf.union("a", "b")
    assert uf.find("c") == uf.find("a") == "a"


def test_email_rule_clusters_across_sources() -> None:
    records = [
        _record("crm:1", email="sam@example.com"),
        _record("email:2", email="sam@example.com"),
        _record("merch:3", email="other@example.com"),
    ]
    clusters = deterministic_clusters(records)
    sizes = sorted(len(m) for m in clusters.values())
    assert sizes == [1, 2]


def test_phone_surname_rule_needs_both() -> None:
    records = [
        _record("crm:1", phone="4045551234", last="García"),
        _record("ticketing:2", phone="4045551234", last="Garcia"),  # folded match
        _record("merch:3", phone="4045551234", last="Different"),
    ]
    clusters = deterministic_clusters(records)
    sizes = sorted(len(m) for m in clusters.values())
    assert sizes == [1, 2]


def test_no_rule_no_merge() -> None:
    records = [
        _record("crm:1", email="a@example.com", phone="4040000001"),
        _record("email:2", email="b@example.com", phone="4040000002"),
    ]
    assert all(len(m) == 1 for m in deterministic_clusters(records).values())


def test_fan_id_stable_regardless_of_member_order() -> None:
    assert fan_id_for(["email:2", "crm:1"]) == fan_id_for(["crm:1", "email:2"])
    assert fan_id_for(["crm:1"]).startswith("FAN-")


def test_mode_longest_prefers_frequent_then_longest() -> None:
    assert _mode_longest(["Bill", "William", "William"]) == "William"
    assert _mode_longest(["WILLIAM", "William"]) == "William"  # folded tie -> longest/lex
    assert _mode_longest([]) is None


def test_fold_strips_diacritics_and_case() -> None:
    assert fold("García") == "garcia"
    assert fold("  ") is None


def test_golden_record_survivorship() -> None:
    records = [
        _record(
            "crm:1",
            email="old@example.com",
            first="William",
            observed=datetime(2025, 1, 1, tzinfo=UTC),
        ),
        _record(
            "email:2",
            email="new@example.com",
            first="Bill",
            observed=datetime(2026, 2, 1, tzinfo=UTC),
        ),
        _record(
            "ticketing:3",
            email="new@example.com",
            first="William",
            observed=datetime(2025, 6, 1, tzinfo=UTC),
        ),
    ]
    fan = build_golden(records)
    assert fan.email == "new@example.com"  # latest observed wins
    assert fan.first_name == "William"  # modal name wins over nickname
    assert fan.sources == "crm,email,ticketing"
    assert fan.record_count == 3
