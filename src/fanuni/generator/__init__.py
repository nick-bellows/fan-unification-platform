"""Seeded synthetic-data generator.

Produces the four source systems (CRM, ticketing, merch, email marketing) plus
fixtures reference data, and — separately — the ground-truth entity map that
the unification eval harness scores against. The pipeline itself must never
read the ground truth; that boundary is what keeps the accuracy numbers honest.
"""
