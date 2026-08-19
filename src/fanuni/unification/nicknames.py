"""Nickname canonicalization for matching.

A standard record-linkage resource (public knowledge, not ground truth): maps
common US nickname forms to a canonical formal name so Bill and William agree
at the exact-match level — string similarity alone scores them ~0.66.
"""

from __future__ import annotations

_CANONICAL: dict[str, tuple[str, ...]] = {
    "william": ("bill", "will", "billy"),
    "robert": ("rob", "bob", "bobby"),
    "elizabeth": ("liz", "beth", "lizzie"),
    "margaret": ("peggy", "maggie"),
    "james": ("jim", "jimmy"),
    "jennifer": ("jen", "jenny"),
    "michael": ("mike", "mikey"),
    "katherine": ("kate", "katie", "kathy"),
    "joseph": ("joe", "joey"),
    "christopher": ("chris", "topher"),
    "daniel": ("dan", "danny"),
    "matthew": ("matt",),
    "nicholas": ("nick", "nico"),
    "anthony": ("tony",),
    "andrew": ("drew", "andy"),
    "rebecca": ("becca", "becky"),
    "patricia": ("pat", "trish"),
    "richard": ("rick", "rich"),
    "thomas": ("tom", "tommy"),
    "charles": ("charlie", "chuck"),
    "steven": ("steve",),
    "edward": ("ed", "eddie", "ted"),
    "alexander": ("alex", "xander"),
    "samantha": ("sam",),
    "benjamin": ("ben", "benny"),
    "jonathan": ("jon", "jonny"),
    "timothy": ("tim", "timmy"),
    "gregory": ("greg",),
    "jessica": ("jess", "jessie"),
    "amanda": ("mandy",),
    "susan": ("sue", "susie"),
    "deborah": ("deb", "debbie"),
    "kimberly": ("kim",),
    "victoria": ("vicky", "tori"),
    "ronald": ("ron", "ronnie"),
    "kenneth": ("ken", "kenny"),
    "joshua": ("josh",),
    "zachary": ("zach",),
    "nathaniel": ("nate", "nathan"),
    "abigail": ("abby",),
    "gabriella": ("gabby",),
    "isabella": ("bella", "izzy"),
    "alexandra": ("lexi", "sasha"),
    "cassandra": ("cassie",),
    "frederick": ("fred", "freddie"),
    "lawrence": ("larry",),
    "raymond": ("ray",),
    "dorothy": ("dot", "dottie"),
    "barbara": ("barb",),
    "leonardo": ("leo",),
}

NICKNAME_TO_CANONICAL: dict[str, str] = {
    nick: formal for formal, nicks in _CANONICAL.items() for nick in nicks
}


def canonical_first_name(folded: str | None) -> str | None:
    """Map a folded first name to its canonical formal form."""
    if folded is None:
        return None
    return NICKNAME_TO_CANONICAL.get(folded, folded)
