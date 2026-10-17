"""The version-control port -- the one place the kit asks the repository what it carries.

Two readings need it and must never disagree: the ratchet's previous ACCEPTED state, and the set
of files a reading may depend on (ADR-021 decision 8). A reading of the tree that counted a file
the repository does not carry -- a dependency directory, a build output -- would change the day
someone ran an install, and read stale on every clean clone with nothing about the host having
moved. So both readings go through here, and so does every later one.

Bytes are decoded here and nowhere else, as UTF-8 and never as the machine's locale: two sides
agreeing on a name and disagreeing on its encoding is the failure that reads as a thing simply not
being there (Cardinal VII). A missing tool, a tree that is not a repository and a path that is not
in HEAD all arrive as the same kind of answer -- a REASON, which the caller states instead of
guessing past it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def run(root, argv: list) -> tuple:
    """`(what version control said, None)` or `(None, why it could not say it)`."""
    try:
        done = subprocess.run(["git", "-C", str(root), *argv], capture_output=True)
    except (OSError, ValueError) as exc:
        return None, f"git could not be run over this tree -- {exc}"
    if done.returncode != 0:
        said = done.stderr.decode("utf-8", "replace").strip()
        return None, said or f"git exited {done.returncode} and said nothing"
    return done.stdout.decode("utf-8", "replace"), None


def carried(root) -> "list | None":
    """Every file the repository at `root` carries or would carry: tracked, plus untracked and not
    ignored -- host-relative, `/`-separated, sorted. `None` where no repository answers: the caller
    then reads the filesystem, and says nothing it could not have read either way."""
    said, _why = run(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if said is None:
        return None
    return sorted({p for p in said.split("\0") if p})


def tracked(root) -> "list | None":
    """Every file the repository at `root` TRACKS -- what a clone receives, never an untracked file
    a person left beside it -- host-relative, `/`-separated, sorted; `None` where no repository
    answers (the whole-tree audit, ADR-024 decision 20)."""
    said, _why = run(root, ["ls-files", "-z", "--cached"])
    if said is None:
        return None
    return sorted({p for p in said.split("\0") if p})


def _paths(root, argv: list) -> tuple:
    said, why = run(root, argv)
    return (None, why) if said is None else ([p for p in said.split("\0") if p], None)


def _born(root) -> bool:
    return run(root, ["rev-parse", "--verify", "--quiet", "HEAD"])[0] is not None


def staged_paths(root) -> tuple:
    """`(paths, None)` the next commit records -- the index against HEAD, or the whole index before
    the first commit -- or `(None, why)`. A merge being recorded is weighed by what differs from EVERY
    parent: what the merged branch brought was weighed where it was made, and only what the merge
    itself adds (a resolution, an evil merge) is new."""
    if not _born(root):
        return _paths(root, ["ls-files", "-z"])
    ours = _paths(root, ["diff", "--cached", "--no-renames", "--name-only", "-z", "HEAD", "--"])
    if ours[0] is None or run(root, ["rev-parse", "--verify", "--quiet", "MERGE_HEAD"])[0] is None:
        return ours
    theirs = _paths(root, ["diff", "--cached", "--no-renames", "--name-only", "-z", "MERGE_HEAD", "--"])
    return (None, theirs[1]) if theirs[0] is None else (sorted(set(ours[0]) & set(theirs[0])), None)


def staged_text(root, rel: str) -> tuple:
    """`(text, None)` of a file as the index holds it -- what the commit records -- or `(None, why)`."""
    return run(root, ["show", f":{rel}"])


def working_paths(root) -> tuple:
    """`(paths, None)` of the working change -- what differs from HEAD, staged or not, and what is
    untracked and not ignored -- or `(None, why)`."""
    tracked = (_paths(root, ["diff", "--no-renames", "--name-only", "-z", "HEAD", "--"]) if _born(root)
               else _paths(root, ["ls-files", "-z"]))
    others = _paths(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    for found in (tracked, others):
        if found[0] is None:
            return found
    return sorted(set(tracked[0]) | set(others[0])), None


def range_paths(root, base: str, head: str) -> tuple:
    """`(paths, None)` changed between two revisions, or `(None, why)`."""
    return _paths(root, ["diff", "--no-renames", "--name-only", "-z", base, head, "--"])


def commits_between(root, base, head: str) -> tuple:
    """`(shas, None)` oldest first -- every commit reachable from `head` and not from `base` (every
    commit reachable from `head` when there is no base) -- or `(None, why)`."""
    said, why = run(root, ["rev-list", "--reverse", head] + ([f"^{base}"] if base else []))
    return (None, why) if said is None else (said.split(), None)


def commits_unpublished(root, head: str, published_as: str) -> tuple:
    """`(shas, None)` oldest first -- every commit reachable from `head` that no remote-tracking ref
    carries other than `published_as` (the ref `head` is being pushed as) and the remotes' HEAD -- or
    `(None, why)`. What a first push of a branch brings that the remote did not already hold."""
    name = published_as[len("refs/remotes/"):] if published_as.startswith("refs/remotes/") else published_as
    remote = name.split("/", 1)[0]
    said, why = run(root, ["rev-list", "--reverse", head, f"--exclude={name}", f"--exclude={remote}/HEAD",
                           "--not", "--remotes"])
    return (None, why) if said is None else (said.split(), None)


def commit_paths(root, sha: str) -> tuple:
    """`(paths, None)` one commit changed -- against its parent, against nothing for a root, and for a
    merge only what differs from EVERY parent (`--cc`), which is what the merge itself introduced."""
    return _paths(root, ["diff-tree", "--cc", "--no-commit-id", "--name-only", "-r", "-z", "--no-renames", "--root", sha])


def commit_message(root, sha: str) -> tuple:
    return run(root, ["log", "-1", "--format=%B", sha])


def history(root, rel: str, follow: bool = False) -> tuple:
    """`([(sha, path)], None)` -- every commit on HEAD's history that touched `rel`, OLDEST first, with the
    path the file had in that commit (renames followed when `follow`) -- or `(None, why)`."""
    said, why = run(root, ["log", *(["--follow"] if follow else []), "--format=%x01%H", "--name-only", "--", rel])
    if said is None:
        return None, why
    out, sha = [], None
    for line in said.splitlines():
        if line.startswith("\x01"):
            sha = line[1:].strip()
        elif line.strip() and sha:
            out.append((sha, line.strip()))
            sha = None
    return list(reversed(out)), None


def parent(root, sha: str) -> str:
    """The first parent of a commit, or "" for a root commit."""
    said, _why = run(root, ["rev-parse", "--verify", "-q", f"{sha}^"])
    return (said or "").strip()


def order(root) -> dict:
    """{sha: position} of every commit on HEAD's history, oldest first and every parent before its
    children -- what came before what."""
    said, _why = run(root, ["rev-list", "--topo-order", "--reverse", "HEAD"])
    return {sha: index for index, sha in enumerate((said or "").split())}


def verdict(root, sha: str, signers_text: str) -> tuple:
    """(git's verdict on one commit's signature, the principal it names), read against an allowed-signers
    TEXT -- the trust root as it stood where the caller says, never the one the tree holds now. `G` is
    good; anything else is not one. git verifies; nothing here does."""
    import os
    import tempfile
    handle, held = tempfile.mkstemp(prefix="kit-signers-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as out:
            out.write(signers_text or "")
        said, _why = run(root, ["-c", "gpg.format=ssh", "-c", f"gpg.ssh.allowedSignersFile={Path(held).as_posix()}",
                                "log", "-1", "--format=%G?%x09%GS", sha])
    finally:
        os.unlink(held)
    verdict_, _, principal = (said or "").strip().partition("\t")
    return verdict_, principal


def global_setting(root, name: str) -> str:
    """A setting of the user's own git configuration, "" where it is unset."""
    said, _why = run(root, ["config", "--global", "--get", name])
    return (said or "").strip()


def version(root) -> tuple:
    """(major, minor) of the version control on this machine, (0, 0) where none answers."""
    said, _why = run(root, ["version"])
    found = re.search(r"(\d+)\.(\d+)", said or "")
    return (int(found.group(1)), int(found.group(2))) if found else (0, 0)


def configure(root, settings: dict) -> tuple:
    """Write each setting into this repository's own configuration (never the user's); `(True, None)`
    or `(None, why)`."""
    for name, value in settings.items():
        said, why = run(root, ["config", "--local", name, value])
        if said is None:
            return None, why
    return True, None


def unpushed_paths(root) -> tuple:
    """`(paths, None)` every commit on HEAD brings that its upstream does not hold -- or, with no upstream,
    that no remote holds -- or `(None, why)`. What a push carries, and so what it has to prove."""
    upstream, _ = run(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream:
        base, why = run(root, ["merge-base", upstream.strip(), "HEAD"])
        if base is None:
            return None, why
        return range_paths(root, base.strip(), "HEAD")
    shas, why = run(root, ["rev-list", "HEAD", "--not", "--remotes"])
    if shas is None:
        return None, why
    paths = set()
    for sha in shas.split():
        said, why = commit_paths(root, sha)
        if said is None:
            return None, why
        paths |= set(said)
    return sorted(paths), None


def clean_tree(root) -> "str | None":
    """The id of the tree HEAD holds, when the working tree holds exactly it -- nothing staged, changed
    or untracked-and-not-ignored -- else None: the bytes a command just read have one name only then."""
    said, _why = run(root, ["status", "--porcelain", "--untracked-files=normal"])
    if said is None or said.strip():
        return None
    tree, _why = run(root, ["rev-parse", "HEAD^{tree}"])
    return tree.strip() if tree else None


def shallow(root) -> bool:
    """Whether this clone holds only part of its history -- where a commit a reading needs may be absent."""
    said, _why = run(root, ["rev-parse", "--is-shallow-repository"])
    return (said or "").strip() == "true"


def file_at(root, sha: str, rel: str) -> tuple:
    """`(text, None)` the file as the commit holds it, or `(None, why)` where it holds none."""
    return run(root, ["show", f"{sha}:{rel}"])

