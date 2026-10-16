"""The verb table in `kit/README.md` is a projection of the verbs themselves, never a second list.

Each verb declares its own `SUMMARY` and whether it `MUTATES`; the CLI discovers verbs from files and
knows no verb's name. A hand-kept table beside that went on listing eleven verbs after there were
twenty. The table between the two markers is therefore DERIVED here, and this test fails, printing
the table that belongs there, the moment it differs.

    python tests/unit/test_verb_reference.py     # rewrites the table between the markers
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
README = KIT / "README.md"
BEGIN, END = "<!-- verbs:begin -- derived from each verb's SUMMARY and MUTATES -->", "<!-- verbs:end -->"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))


def table() -> str:
    rows = ["| verb | does | writes |", "| --- | --- | --- |"]
    for path in sorted((KIT / "interpreters" / "verbs").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        verb = importlib.import_module(path.stem)
        writes = "yes -- `--plan` prints the writes first" if getattr(verb, "MUTATES", False) else "nothing"
        rows.append(f"| `{path.stem}` | {' '.join(verb.SUMMARY.split())} | {writes} |")
    return "\n".join(rows)


def _split(text: str) -> tuple:
    head, rest = text.split(BEGIN, 1)
    _old, tail = rest.split(END, 1)
    return head, tail


def test_the_verb_table_is_the_verbs_own_declaration():
    head, tail = _split(README.read_text(encoding="utf-8"))
    current = README.read_text(encoding="utf-8")
    expected = f"{head}{BEGIN}\n{table()}\n{END}{tail}"
    assert current == expected, f"kit/README.md's verb table is stale; it should read:\n{table()}"


if __name__ == "__main__":
    head, tail = _split(README.read_text(encoding="utf-8"))
    README.write_text(f"{head}{BEGIN}\n{table()}\n{END}{tail}", encoding="utf-8", newline="\n")
