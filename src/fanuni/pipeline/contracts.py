"""Ingestion contracts: per-source pandera schemas over the wire format.

CSV sources validate as strings (that's what arrives); JSONL sources validate
native types. Rows failing a contract go to raw.quarantine with the reason;
a missing required column rejects the whole file (that's how the merch schema
drift would have surfaced had the loader not been taught both forms).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
import pandera.pandas as pa

_ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _matches(pattern: re.Pattern[str]) -> pa.Check:
    return pa.Check(
        lambda v: isinstance(v, str) and bool(pattern.match(v)),
        element_wise=True,
        error=f"must match {pattern.pattern}",
    )


def _id_like(prefix: str) -> pa.Check:
    return pa.Check(
        lambda v: isinstance(v, str) and v.startswith(prefix),
        element_wise=True,
        error=f"must start with {prefix}",
    )


_EMAIL = pa.Check(
    lambda v: isinstance(v, str) and "@" in v and "." in v.rsplit("@", 1)[-1],
    element_wise=True,
    error="must look like an email address",
)

_POSITIVE_NUMBER = pa.Check(
    lambda v: isinstance(v, int | float) and not isinstance(v, bool) and v > 0,
    element_wise=True,
    error="must be a positive number",
)

_NUMERIC_STRING = pa.Check(
    lambda v: isinstance(v, str) and v != "" and float(v) >= 0,
    element_wise=True,
    error="must be a non-negative numeric string",
)


def _col(*checks: pa.Check, required: bool = True, nullable: bool = False) -> pa.Column:
    return pa.Column(object, list(checks), required=required, nullable=nullable, coerce=False)


SCHEMAS: dict[str, pa.DataFrameSchema] = {
    "crm_contacts": pa.DataFrameSchema(
        {
            "Id": _col(_id_like("003")),
            "LastName": _col(),
            "Email": _col(_EMAIL, nullable=True),
            "SystemModstamp": _col(_matches(_ISO_TS)),
            "Birthdate": _col(_matches(_ISO_DATE), nullable=True),
        },
        strict=False,
        unique=["Id"],
    ),
    "crm_opportunities": pa.DataFrameSchema(
        {
            "Id": _col(_id_like("006")),
            "ContactId": _col(_id_like("003")),
            "Amount": _col(_POSITIVE_NUMBER),
            "Type": _col(pa.Check.isin(["Membership", "Donation"])),
            "CloseDate": _col(_matches(_ISO_DATE)),
            "SystemModstamp": _col(_matches(_ISO_TS)),
        },
        strict=False,
        unique=["Id"],
    ),
    "ticketing_orders": pa.DataFrameSchema(
        {
            "order_id": _col(_id_like("T-")),
            "match_id": _col(_id_like("MTCH-")),
            "purchased_at": _col(_matches(_ISO_TS)),
            "qty": _col(
                pa.Check(
                    lambda v: isinstance(v, int) and 1 <= v <= 10,
                    element_wise=True,
                    error="qty must be an int in 1..10",
                )
            ),
            "total": _col(_POSITIVE_NUMBER),
            "purchaser_name": _col(),
            "purchaser_email": _col(_EMAIL),
        },
        strict=False,
        unique=["order_id"],
    ),
    "merch_order_items": pa.DataFrameSchema(
        {
            "order_number": _col(_id_like("M-")),
            "created_at": _col(_matches(_ISO_TS)),
            "customer_email": _col(_EMAIL),
            "billing_name": _col(),
            "quantity": _col(_NUMERIC_STRING),
            "unit_price": _col(_NUMERIC_STRING),
            # Present pre-drift / post-drift respectively; the loader accepts both.
            "billing_zip": _col(required=False, nullable=True),
            "billing_postal_code": _col(required=False, nullable=True),
            "discount_code": _col(required=False, nullable=True),
        },
        strict=False,
    ),
    "email_subscribers": pa.DataFrameSchema(
        {
            "subscriber_id": _col(_id_like("S-")),
            "email": _col(_EMAIL),
            "signup_date": _col(_matches(_ISO_DATE)),
            "status": _col(pa.Check.isin(["subscribed", "unsubscribed"])),
        },
        strict=False,
        unique=["subscriber_id"],
    ),
    "email_events": pa.DataFrameSchema(
        {
            "event_id": _col(_id_like("E-")),
            "subscriber_id": _col(_id_like("S-")),
            "campaign_id": _col(_id_like("C-")),
            "event_type": _col(pa.Check.isin(["send", "open", "click"])),
            "occurred_at": _col(_matches(_ISO_TS)),
        },
        strict=False,
        unique=["event_id"],
    ),
    "email_campaigns": pa.DataFrameSchema(
        {
            "campaign_id": _col(_id_like("C-")),
            "name": _col(),
            "sent_at": _col(_matches(_ISO_TS)),
        },
        strict=False,
        unique=["campaign_id"],
    ),
    "fixtures": pa.DataFrameSchema(
        {
            "match_id": _col(_id_like("MTCH-")),
            "kickoff_at": _col(_matches(_ISO_TS)),
            "home_team": _col(),
            "away_team": _col(),
        },
        strict=False,
        unique=["match_id"],
    ),
}


def validate_rows(
    source_key: str, rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    """Split rows into (accepted, rejected-with-reason) under the contract."""
    if not rows:
        return [], []
    schema = SCHEMAS[source_key]
    df = pd.DataFrame(rows, dtype=object)
    # CSV empty strings mean "absent" for nullable checks.
    df = df.where(df.notna(), None).replace({"": None})
    try:
        schema.validate(df, lazy=True)
        return rows, []
    except pa.errors.SchemaErrors as errors:
        reasons: dict[int, list[str]] = {}
        whole_file: list[str] = []
        for case in errors.failure_cases.itertuples():
            column = getattr(case, "column", None)
            check = str(getattr(case, "check", "unknown check"))
            index = getattr(case, "index", None)
            if index is None or (isinstance(index, float) and pd.isna(index)):
                failure = getattr(case, "failure_case", None)
                subject = failure if check == "column_in_dataframe" else (column or "schema")
                whole_file.append(f"{subject}: {check}")
            else:
                reasons.setdefault(int(index), []).append(f"{column}: {check}")
        if whole_file:
            reason = "; ".join(sorted(set(whole_file)))
            return [], [(row, reason) for row in rows]
        good = [row for i, row in enumerate(rows) if i not in reasons]
        bad = [(rows[i], "; ".join(sorted(set(msgs)))) for i, msgs in sorted(reasons.items())]
        return good, bad
