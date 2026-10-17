"""The release-source port -- a kit read from a DECLARED revision of a repository, and returned only if it is
a release (ADR-016).

The boundary at which the kit stops being the directory it was handed and becomes the bytes of a
published revision: version control and an archive are reached here and nowhere else, so the core
that judges a release (`pin`) holds no subprocess, no archive and no scratch of its own. The entry
point is the one caller: a release SOURCE is resolved before any context exists.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import pin
import vcs as vcs_port
from manifest import Manifest

#: A release source naming a revision of a repository, in the form the Python packaging field
#: standardised for exactly this (PEP 508 / pip's VCS form): `git+<repo>@<rev>#subdirectory=<dir>`.
_VCS = re.compile(r"^git\+(?P<repo>.+)@(?P<rev>[^@#]+)(#subdirectory=(?P<sub>[^#]+))?$")


def is_source(text: str) -> bool:
    """Whether a `--kit` value names a release SOURCE (a revision) rather than a directory."""
    return bool(_VCS.match(text or ""))


# -- a release source --------------------------------------------------------------------------
def fetch(source: str, into: Path) -> Path:
    """A release, read from a DECLARED revision into `into`, and returned only if it IS one.

    `git+<repo>@<rev>#subdirectory=<dir>` is read with `git archive` at exactly that revision --
    never a working tree, and with nothing the standard library and git cannot stand behind."""
    vcs = _VCS.match(source)
    if vcs is None:
        raise pin.ReleaseError(f"release source {source!r}: not of the form "
                           f"git+<repo>@<rev>#subdirectory=<dir>")
    repo, rev, sub = vcs["repo"], vcs["rev"], (vcs["sub"] or ".").strip("/")
    if not Path(repo).is_dir():
        # A repository that is not on this machine (https://, ssh://, git@host:, file://) is
        # cloned bare into the scratch first: `git archive --remote` is refused by most hosts,
        # and what is read is still exactly the named revision, never a working tree.
        local = into / "source.git"
        cloned = subprocess.run(["git", "clone", "--bare", "--quiet", repo, str(local)],
                                capture_output=True, text=True, env=vcs_port.env())
        if cloned.returncode != 0:
            raise pin.ReleaseError(f"release source {source!r}: the repository could not be cloned -- "
                               f"{cloned.stderr.strip()}")
        repo = str(local)
    archive = into / "release.tar"
    done = subprocess.run(["git", "-C", repo, "archive", "--format=tar", "-o", str(archive),
                           rev, sub], capture_output=True, text=True, env=vcs_port.env())
    if Path(repo) == into / "source.git":
        remove_tree(into / "source.git")  # read: only the named revision's bytes go on
    if done.returncode != 0:
        raise pin.ReleaseError(f"release source {source!r}: git archive refused -- "
                           f"{done.stderr.strip()}")
    with tarfile.open(archive) as tar:
        tar.extractall(into / "tree", filter="data")
    kit = (into / "tree" / sub).resolve()
    if not (kit / "MANIFEST.json").is_file():
        raise pin.ReleaseError(f"release source {source!r}: no MANIFEST.json at {sub!r}")
    seen = pin.reading(Manifest(kit))
    if not seen["released"]:
        raise pin.ReleaseError(
            f"release source {source!r} is not a release: {len(seen['drift'])} path(s) differ "
            f"from its own lock -- " + ", ".join(f"{p} ({s})" for s, p, _ in seen["drift"][:5]))
    return kit


def remove_tree(path: Path) -> None:
    """Remove a scratch tree, read-only files included: a git object store marks its packs
    read-only, and on Windows a plain removal leaves them behind, and the scratch with them."""
    def writable(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=writable)
    else:
        shutil.rmtree(path, onerror=writable)


def fetched(source: str) -> tuple:
    """(kit, scratch): `fetch` into a fresh directory OUTSIDE every host. The caller removes
    `scratch` when the run ends, refused or not."""
    scratch = Path(tempfile.mkdtemp(prefix="kit-release-"))
    try:
        return fetch(source, scratch), scratch
    except BaseException:
        remove_tree(scratch)
        raise
