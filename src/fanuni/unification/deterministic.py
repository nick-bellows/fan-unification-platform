"""Deterministic pass: high-precision exact rules via union-find.

Rule 1 — identical normalized email.
Rule 2 — identical phone AND identical folded surname.

Known, deliberate weaknesses the eval quantifies: shared household emails
over-merge family members (rule 1), and a changed email with no other overlap
under-merges (neither rule fires). The probabilistic pass exists for the
second; the first is the precision price of email matching.
"""

from __future__ import annotations

from collections import defaultdict

from fanuni.unification.records import IdentityRecord, fold


class UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        parent = self._parent.setdefault(item, item)
        if parent != item:
            self._parent[item] = self.find(parent)
        return self._parent[item]

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            # Deterministic tie-break keeps cluster roots (and downstream
            # fan_ids) stable across runs.
            low, high = sorted((root_a, root_b))
            self._parent[high] = low

    def clusters(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in self._parent:
            grouped[self.find(item)].append(item)
        return {root: sorted(members) for root, members in grouped.items()}


def deterministic_clusters(records: list[IdentityRecord]) -> dict[str, list[str]]:
    """Cluster record refs; every record appears, singletons included."""
    uf = UnionFind()
    by_email: dict[str, str] = {}
    by_phone_surname: dict[tuple[str, str], str] = {}

    for record in records:
        uf.find(record.ref)  # register even if nothing links it
        if record.email:
            anchor = by_email.setdefault(record.email, record.ref)
            if anchor != record.ref:
                uf.union(anchor, record.ref)
        surname = fold(record.last_name)
        if record.phone and surname:
            key = (record.phone, surname)
            anchor = by_phone_surname.setdefault(key, record.ref)
            if anchor != record.ref:
                uf.union(anchor, record.ref)
    return uf.clusters()
