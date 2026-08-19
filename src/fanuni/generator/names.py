"""Name pools used to make identity resolution realistically hard.

Nickname pairs create records where the same person appears as William and
Bill; the accented pool creates diacritic variants (José vs Jose). Both are
common failure modes for naive exact matching.
"""

from __future__ import annotations

NICKNAMES: dict[str, tuple[str, ...]] = {
    "William": ("Bill", "Will", "Billy"),
    "Robert": ("Rob", "Bob", "Bobby"),
    "Elizabeth": ("Liz", "Beth", "Lizzie"),
    "Margaret": ("Peggy", "Maggie"),
    "James": ("Jim", "Jimmy"),
    "Jennifer": ("Jen", "Jenny"),
    "Michael": ("Mike", "Mikey"),
    "Katherine": ("Kate", "Katie", "Kathy"),
    "Joseph": ("Joe", "Joey"),
    "Christopher": ("Chris", "Topher"),
    "Daniel": ("Dan", "Danny"),
    "Matthew": ("Matt",),
    "Nicholas": ("Nick", "Nico"),
    "Anthony": ("Tony",),
    "Andrew": ("Drew", "Andy"),
    "Rebecca": ("Becca", "Becky"),
    "Patricia": ("Pat", "Trish"),
    "Richard": ("Rick", "Rich"),
    "Thomas": ("Tom", "Tommy"),
    "Charles": ("Charlie", "Chuck"),
    "Steven": ("Steve",),
    "Edward": ("Ed", "Eddie", "Ted"),
    "Alexander": ("Alex", "Xander"),
    "Samantha": ("Sam",),
    "Benjamin": ("Ben", "Benny"),
    "Jonathan": ("Jon", "Jonny"),
    "Timothy": ("Tim", "Timmy"),
    "Gregory": ("Greg",),
    "Jessica": ("Jess", "Jessie"),
    "Amanda": ("Mandy",),
    "Susan": ("Sue", "Susie"),
    "Deborah": ("Deb", "Debbie"),
    "Kimberly": ("Kim",),
    "Victoria": ("Vicky", "Tori"),
    "Ronald": ("Ron", "Ronnie"),
    "Kenneth": ("Ken", "Kenny"),
    "Joshua": ("Josh",),
    "Zachary": ("Zach",),
    "Nathaniel": ("Nate", "Nathan"),
    "Abigail": ("Abby",),
    "Gabriella": ("Gabby",),
    "Isabella": ("Bella", "Izzy"),
    "Alexandra": ("Lexi", "Sasha"),
    "Cassandra": ("Cassie",),
    "Frederick": ("Fred", "Freddie"),
    "Lawrence": ("Larry",),
    "Raymond": ("Ray",),
    "Dorothy": ("Dot", "Dottie"),
    "Barbara": ("Barb",),
    "Leonardo": ("Leo",),
}

# (first, last) pairs carrying diacritics; a soccer federation's fan base is a
# natural place for these, and they exercise the diacritics mess type.
ACCENTED_NAMES: tuple[tuple[str, str], ...] = (
    ("José", "García"),
    ("María", "Rodríguez"),
    ("Andrés", "Muñoz"),
    ("Sofía", "Peña"),
    ("Raúl", "Fernández"),
    ("Verónica", "Núñez"),
    ("Iván", "Ramírez"),
    ("Mónica", "Gutiérrez"),
    ("Óscar", "Martínez"),
    ("Lucía", "Hernández"),
    ("Julián", "Vásquez"),
    ("Inés", "Cortés"),
    ("René", "Ibáñez"),
    ("Camila", "Suárez"),
    ("Sebastián", "Domínguez"),
)
