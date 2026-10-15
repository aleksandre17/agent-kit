"""One discovery of what a declared KIND resolves to -- the mechanism, held once.

A declaration names a kind and a module answers it. That pairing is now made about more than one
subject: which module judges a kind of rule, and which module reads a kind of reference. The LOOP
that finds them may not be written twice, because a second loop is a second answer to the question
*who answers this kind* -- and the drift would be invisible, since each loop would go on reading
correctly from where it stands while the two disagreed (Cardinal III).

So the discovery lives here and knows no kind of its own, no subject and no caller. It is handed a
directory, the name of the entry a module publishes, the noun its caller speaks in, and the refusal
its caller raises -- and it returns what it found. A name two modules claim is refused rather than
ordered, because a name that resolves to two things is not a name.
"""

from __future__ import annotations

import importlib
from pathlib import Path


def registry(where: Path, entry: str, noun: str, clash: type) -> dict:
    """Every kind published under `entry` by the modules in `where`, by the name each declares.

    A module is found because it is THERE, never because a list here mentions it: adding one is a
    file, and the interpreter that reads the result is not edited (Cardinal II).
    """
    found: dict = {}
    owners: dict = {}
    for path in sorted(where.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = importlib.import_module(path.stem)
        for kind, answer in getattr(module, entry, {}).items():
            if kind in found:
                raise clash(
                    f"{noun} {kind!r} is declared by both {owners[kind]!r} and {path.stem!r}"
                )
            owners[kind] = path.stem
            found[kind] = answer
    return found
