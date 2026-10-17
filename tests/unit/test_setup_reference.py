"""The host blueprint in `docs/guide/setup.md` is a projection of the host layout governance declares
(`host-layout.json`), never a second drawing of it: the table between the markers is DERIVED here, and
this test fails, printing the table that belongs there, the moment the two differ.

    python tests/unit/test_setup_reference.py     # rewrites the table between the markers
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "kit" / "capabilities" / "governance" / "host-layout.json"
GUIDE = ROOT / "docs" / "guide" / "setup.md"
BEGIN, END = "<!-- layout:begin -- derived from kit/capabilities/governance/host-layout.json -->", "<!-- layout:end -->"


def table() -> str:
    rows = ["| path | holds | written by | lifecycle | read it when |", "| --- | --- | --- | --- | --- |"]
    for row in json.loads(LAYOUT.read_text(encoding="utf-8"))["entries"]:
        when = (row.get("read_when") or ["-"])[0]
        pending = f" (pending {row['pending']})" if row.get("pending") else ""
        rows.append(f"| `{row['path']}` | {row.get('holds', '-')}{pending} | {row.get('writer', '-')} | "
                    f"{row.get('lifecycle', '-')} | {when} |")
    return "\n".join(rows)


def _split(text: str) -> tuple:
    head, rest = text.split(BEGIN, 1)
    return head, rest.split(END, 1)[1]


def test_the_host_blueprint_is_the_layouts_own_declaration():
    head, tail = _split(GUIDE.read_text(encoding="utf-8"))
    expected = f"{head}{BEGIN}\n{table()}\n{END}{tail}"
    assert GUIDE.read_text(encoding="utf-8") == expected, f"docs/guide/setup.md's blueprint is stale:\n{table()}"


if __name__ == "__main__":
    head, tail = _split(GUIDE.read_text(encoding="utf-8"))
    GUIDE.write_text(f"{head}{BEGIN}\n{table()}\n{END}{tail}", encoding="utf-8", newline="\n")
