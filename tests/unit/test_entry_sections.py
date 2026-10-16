"""A served entry's sections each open their own paragraph -- a pointer as much as a page.

A section that NAMES a page instead of inlining it (ADR-021 decision 5) is one sentence. It must end
its line the way a file's text does, or the next section's heading is glued to it in every rendered
entry, and a reader of the briefing sees one paragraph where the declaration made two.
"""

from __future__ import annotations

import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import runtime  # noqa: E402


class _Workspace:
    def exists(self, rel):
        return False


class _Context:
    workspace = _Workspace()


def test_a_pointer_section_ends_its_line_as_an_inlined_page_does():
    view = {"sections": [{"heading": "Page", "from": "a.md"},
                         {"heading": "Pointer", "from": "b.md", "points": "what b says"}]}
    rows = runtime._sections(_Context(), view, {"a.md": "page text\n", "b.md": "unread\n"})
    assert [row["text"].endswith("\n") for row in rows] == [True, True]
    assert rows[1]["text"] == "Read `b.md` for what b says.\n"
