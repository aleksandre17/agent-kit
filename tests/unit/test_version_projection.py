"""Unit: `kit/VERSION` is a PROJECTION of `kit/MANIFEST.json`'s own `version` field, never a
hand-kept second copy (Cardinal III, ADR-015 "Open from L1": both files existed, hand-synced).

There is no code path that writes `kit/VERSION` from the manifest yet -- `lock` is deliberately
scoped to the one lock path it writes (ADR-... "not a way around `installs`"), and inventing a
second writer for a single plain-text file is not proportionate. This test is the projection: it
holds the two texts EQUAL, so a hand-edit that lets them drift fails here, at the cheapest point,
rather than being discovered by a host reading a stale version.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_kit_version_file_equals_manifest_version():
    manifest = json.loads((REPO / "kit" / "MANIFEST.json").read_text(encoding="utf-8"))
    version_file = (REPO / "kit" / "VERSION").read_text(encoding="utf-8").strip()
    assert version_file == manifest["kit"]["version"], (
        f"kit/VERSION ({version_file!r}) has drifted from kit/MANIFEST.json's kit.version "
        f"({manifest['kit']['version']!r}) -- they are one truth; fix kit/VERSION to match"
    )
