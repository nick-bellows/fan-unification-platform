"""Identity resolution ("unification").

Reads staging.identity_records, clusters records that are the same person,
and rebuilds identity.fan_xref + identity.golden_fans — the only interface
the SQL model layer sees. M3 ships the deterministic pass; M4 layers the
probabilistic (Splink) pass on top and measures both against ground truth.
"""
