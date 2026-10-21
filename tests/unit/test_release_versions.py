"""A published capability whose bytes moved since the last release moves its version too. A host pins a
capability by version and bytes, and a take refuses changed bytes under a pinned version (KIT0032) -- so a
release that changed a bundle and kept its version could not be taken at all. Caught here, before release,
not at the host that takes it."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PUBLISHED = ("adapters", "bundles", "policies", "kit/capabilities")


def _git(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *argv], capture_output=True, text=True, encoding="utf-8")


def _previous_release() -> "str | None":
    """The newest release tag behind HEAD that is not HEAD itself -- what a host may already hold."""
    head = _git("rev-parse", "HEAD").stdout.strip()
    for tag in _git("tag", "--list", "v*", "--sort=-v:refname").stdout.split():
        commit = _git("rev-list", "-n1", tag).stdout.strip()
        if commit != head and _git("merge-base", "--is-ancestor", commit, "HEAD").returncode == 0:
            return tag
    return None


def test_a_capability_whose_bytes_moved_since_the_last_release_moved_its_version():
    if _git("rev-parse", "--git-dir").returncode != 0:
        pytest.skip("not a git checkout: there is no release to compare with")
    previous = _previous_release()
    if previous is None:
        pytest.skip("no earlier release tag: nothing a host could hold yet")
    unmoved = []
    for declaration in sorted(p for root in PUBLISHED for p in (REPO / root).glob("*/capability.json")):
        home = declaration.parent.relative_to(REPO).as_posix()
        then = _git("show", f"{previous}:{home}/capability.json")
        if then.returncode != 0:
            continue  # new since that release: no host holds it
        if _git("diff", "--quiet", previous, "--", home).returncode == 0:
            continue  # the same bytes
        before = json.loads(then.stdout)["version"]
        now = json.loads(declaration.read_text(encoding="utf-8"))["version"]
        if before == now:
            unmoved.append(f"{home}: changed since {previous} and still {now}")
        # A declaration a capability points at (its lifecycle, a policy) carries its own version: the
        # bytes of it moving under the same version is the same refusal one file down.
        for sibling in sorted(declaration.parent.glob("*.json")):
            if sibling.name == "capability.json":
                continue
            rel = sibling.relative_to(REPO).as_posix()
            old = _git("show", f"{previous}:{rel}")
            if old.returncode != 0 or _git("diff", "--quiet", previous, "--", rel).returncode == 0:
                continue
            try:
                old_v = json.loads(old.stdout).get("version")
                new_v = json.loads(sibling.read_text(encoding="utf-8")).get("version")
            except (ValueError, AttributeError):
                continue
            if old_v is not None and old_v == new_v:
                unmoved.append(f"{rel}: changed since {previous} and still {new_v}")
    assert unmoved == [], unmoved
