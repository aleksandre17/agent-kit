"""Unit: a briefing section with a DEPRECATED source serves it while the host holds it, and its
successor once it is gone (ADR-024 decision 21) -- one source in force, never both."""

from __future__ import annotations

import sys
import types
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import laws  # noqa: E402
import serve  # noqa: E402

SECTION = {"id": "project-laws", "heading": "h", "from": "gen/LAWS.md", "deprecated_from": "host/laws.md"}


def _ctx(files: dict):
    workspace = types.SimpleNamespace(exists=lambda rel: rel in files, read_text=lambda rel: files[rel])
    return types.SimpleNamespace(workspace=workspace)


def test_the_deprecated_page_is_served_while_present_and_the_rendered_list_after():
    produced = {"gen/LAWS.md": "1. **Rendered.** from rules\n"}
    held = serve._sections(_ctx({"host/laws.md": "1. **Old.** prose\n"}), {"sections": [SECTION]}, produced)
    assert held[0]["from"] == "host/laws.md" and "Old" in held[0]["text"]
    moved = serve._sections(_ctx({}), {"sections": [SECTION]}, produced)
    assert moved[0]["from"] == "gen/LAWS.md" and "Rendered" in moved[0]["text"]


def test_a_page_is_read_into_rules_the_host_completes():
    page = "<!-- c -->\n1. **A.** says a\n   more. *Gate `x`.*\n2. **B.** says b.\n3. _(none declared yet)_\n"
    made = laws.rules(page, "host@1.0.0", "who", "rule", 1)
    assert [(r["law"], r["title"], r["says"], r.get("enforcement_note")) for r in made] == [
        (1, "A.", "says a more.", "Gate `x`."), (2, "B.", "says b.", None)]
    assert all("derives_from" not in r and r["id"] == f"host@1.0.0#law-{r['law']}" for r in made)
