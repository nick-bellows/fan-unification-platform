from fanuni.pipeline.contracts import validate_rows
from fanuni.pipeline.flows import batch_month, next_watermark, parse_rows
from fanuni.pipeline.salesforce import build_soql


def test_build_soql_without_watermark() -> None:
    assert build_soql("Contact", None) == "SELECT Fields(ALL) FROM Contact ORDER BY SystemModstamp"


def test_build_soql_with_watermark() -> None:
    soql = build_soql("Opportunity", "2026-01-01T00:00:00Z")
    assert "WHERE SystemModstamp > 2026-01-01T00:00:00Z" in soql


def test_batch_month() -> None:
    assert batch_month("orders_2025-03.jsonl") == "2025-03"
    assert batch_month("subscribers_2026-01.csv") == "2026-01"
    assert batch_month("fixtures.csv") is None


def test_parse_rows_jsonl_and_csv() -> None:
    jsonl = b'{"a": 1}\n{"a": 2}\n'
    assert parse_rows("jsonl", jsonl) == [{"a": 1}, {"a": 2}]
    csv_body = b"x,y\n1,hello\n2,world\n"
    assert parse_rows("csv", csv_body) == [
        {"x": "1", "y": "hello"},
        {"x": "2", "y": "world"},
    ]


def _order(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "order_id": "T-000001",
        "match_id": "MTCH-0001",
        "purchased_at": "2026-01-05T12:00:00Z",
        "channel": "web",
        "section": "Sideline",
        "qty": 2,
        "unit_price": 75.0,
        "total": 150.0,
        "purchaser_name": "Sam Example",
        "purchaser_email": "sam@example.com",
        "purchaser_zip": "30303",
    }
    row.update(overrides)
    return row


def test_validate_rows_accepts_clean_rows() -> None:
    good, bad = validate_rows("ticketing_orders", [_order(), _order(order_id="T-000002")])
    assert len(good) == 2 and bad == []


def test_validate_rows_quarantines_bad_rows_with_reason() -> None:
    rows = [_order(), _order(order_id="T-000002", qty=99), _order(order_id="X-1")]
    good, bad = validate_rows("ticketing_orders", rows)
    assert [r["order_id"] for r in good] == ["T-000001"]
    reasons = {r[0]["order_id"]: r[1] for r in bad}
    assert "qty" in reasons["T-000002"]
    assert "order_id" in reasons["X-1"]


def test_validate_rows_missing_required_column_rejects_file() -> None:
    rows = [{k: v for k, v in _order().items() if k != "purchaser_email"}]
    good, bad = validate_rows("ticketing_orders", rows)
    assert good == []
    assert len(bad) == 1 and "purchaser_email" in bad[0][1]


def test_validate_rows_accepts_both_merch_schemas() -> None:
    pre = {
        "order_number": "M-000001",
        "created_at": "2025-10-01T10:00:00Z",
        "customer_email": "a@example.com",
        "billing_name": "A Example",
        "billing_zip": "75001",
        "sku": "SCARF-CL",
        "item_name": "Classic Scarf",
        "quantity": "1",
        "unit_price": "24.99",
        "line_total": "24.99",
    }
    post = dict(pre, order_number="M-000002", discount_code="FAN10")
    post["billing_postal_code"] = post.pop("billing_zip")
    for row in (pre, post):
        good, bad = validate_rows("merch_order_items", [row])
        assert bad == [] and len(good) == 1


def test_next_watermark_advances_over_clean_accepts() -> None:
    assert next_watermark(["t1", "t2"], [], None) == "t2"
    assert next_watermark(["t1", "t2"], [], "t1") == "t2"


def test_next_watermark_never_passes_a_rejected_row() -> None:
    # Reject at t1, accept at t2: advancing to t2 would strand the corrected
    # t1 row (same modstamp) forever — the exact review finding.
    assert next_watermark(["t2"], ["t1"], None) is None
    # Accepts strictly before the earliest reject are safe.
    assert next_watermark(["t0", "t2"], ["t1"], None) == "t0"
    assert next_watermark(["t0", "t2"], ["t1", "t3"], None) == "t0"


def test_next_watermark_does_not_regress_or_move_without_accepts() -> None:
    assert next_watermark([], ["t1"], "t5") is None
    assert next_watermark([], [], None) is None
    assert next_watermark(["t3"], [], "t5") is None  # never move backwards
