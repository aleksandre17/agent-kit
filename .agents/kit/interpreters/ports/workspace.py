"""Workspace port -- every filesystem effect, and the scope that bounds it.

Two responsibilities that are really one: the host root is resolved ONCE at the boundary (a path
is a name, and a name is not a referent until it has been measured), and every write is checked
against a DECLARED scope. A capability may write only inside the targets its own declaration
lists; anything else is refused, loudly, before the byte is written. The port holds no knowledge
of which capability it is serving -- the scope arrives as data.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path, PurePosixPath

from errors import KitError


#: A reader holding the target open is the one condition under which a rename is refused, and
#: only on Windows, where an open file cannot be replaced. The reader is transient -- a poll, an
#: editor, an indexer -- so the rename is retried for a bounded moment, and then the refusal is
#: raised as what it is, never swallowed into a write that silently did not happen.
_REPLACE_ATTEMPTS = 50
_REPLACE_PAUSE = 0.02


def _replace(source: Path, target: Path) -> None:
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(_REPLACE_PAUSE)


class WorkspaceError(KitError):
    """A path could not be resolved inside this workspace."""

    code = "KIT0017"


class WriteScopeError(WorkspaceError):
    """A write was attempted outside the declared scope. Refused, not warned about."""

    code = "KIT0018"


def _normalise(rel: str) -> str:
    """One canonical form for a host-relative path: POSIX separators, no drift."""
    if not rel or rel.strip() != rel:
        raise WorkspaceError(f"not a usable relative path: {rel!r}")
    text = rel.replace("\\", "/")
    pure = PurePosixPath(text)
    if pure.is_absolute() or ".." in pure.parts:
        raise WorkspaceError(f"path must stay inside the workspace: {rel!r}")
    return pure.as_posix()


class Workspace:
    """Rooted, scope-enforcing filesystem access. Reads are unbounded; writes are not."""

    def __init__(self, root: Path, scope: tuple[str, ...] | None = None) -> None:
        self._root = Path(root).resolve()
        self._scope = scope

    @property
    def root(self) -> Path:
        return self._root

    @property
    def scope(self) -> tuple[str, ...] | None:
        return self._scope

    def scoped(self, targets) -> "Workspace":
        """A view of this workspace whose writes are confined to `targets` (files or dirs)."""
        return Workspace(self._root, tuple(sorted(_normalise(t) for t in targets)))

    def unscoped(self) -> "Workspace":
        return Workspace(self._root, None)

    # -- resolution -------------------------------------------------------------------------
    def path(self, rel: str) -> Path:
        return self._root / _normalise(rel)

    def _permit(self, rel: str) -> str:
        norm = _normalise(rel)
        if self._scope is None:
            return norm
        for allowed in self._scope:
            if norm == allowed or norm.startswith(allowed.rstrip("/") + "/"):
                return norm
        raise WriteScopeError(
            f"write refused: {norm!r} is outside the declared scope {list(self._scope)!r}"
        )

    # -- reading ----------------------------------------------------------------------------
    def exists(self, rel: str) -> bool:
        return self.path(rel).exists()

    def read_bytes(self, rel: str) -> bytes:
        """The file as it actually is. Text decoding is a translation, and whoever must MEASURE a
        boundary -- a line ending, a digest -- has to stand before it, not after it."""
        return self.path(rel).read_bytes()

    def read_text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def read_json(self, rel: str):
        return json.loads(self.read_text(rel))

    def carried(self) -> "list[str] | None":
        """Every file the repository at this root carries or would carry -- tracked, plus untracked
        and not ignored -- or `None` where no repository answers. Read once per workspace: a run
        asks this many times and the answer cannot change under a reading."""
        if not hasattr(self, "_carried"):
            import vcs
            self._carried = vcs.carried(self._root)
        return self._carried

    def tracked(self) -> "list[str] | None":
        """Every file the repository at this root tracks, or `None` where no repository answers."""
        if not hasattr(self, "_tracked"):
            import vcs
            self._tracked = vcs.tracked(self._root)
        return self._tracked

    def accepted_listing(self, space: str) -> tuple:
        """(the file names under `space` at HEAD, None) or (None, why) -- the previous ACCEPTED state
        of a place, what HEAD holds and never what the tree holds now (ADR-019)."""
        import vcs
        return vcs.run(self._root, ["ls-tree", "-r", "--name-only", "--full-tree", f"HEAD:./{space}"])

    def accepted_text(self, rel: str) -> tuple:
        """(the text of `rel` at HEAD, None) or (None, why)."""
        import vcs
        return vcs.run(self._root, ["show", f"HEAD:./{rel}"])

    def revision(self, rel: str) -> tuple:
        """(the commit the repository holding `rel` has checked out, its top level relative to this
        root, None) or (None, None, why) -- how a host states the commit of a kit it holds in its own
        tree (a submodule) without the core running a tool (ADR-024 decision 18)."""
        import vcs
        sha, why = vcs.run(self.path(rel), ["rev-parse", "HEAD"])
        top, why_top = vcs.run(self.path(rel), ["rev-parse", "--show-toplevel"])
        if sha is None or top is None:
            return None, None, why or why_top
        try:
            at = Path(top.strip()).resolve().relative_to(self._root.resolve()).as_posix()
        except ValueError:
            return None, None, f"{rel} lies in a repository outside this host ({top.strip()})"
        return sha.strip(), at, None

    def changes(self, rel: str) -> tuple:
        """(every uncommitted change under `rel` as its repository reports it, None) or (None, why)."""
        import vcs
        said, why = vcs.run(self.path(rel), ["status", "--porcelain", "--untracked-files=all", "--", "."])
        return (None, why) if said is None else ([line for line in said.splitlines() if line.strip()], None)

    def files_under(self, rel: str) -> list[str]:
        """Every file below `rel`, host-relative, POSIX-formed, sorted. Directories are not
        classified: a directory is the shape of the tree, a file is the thing that ships."""
        base = self.path(rel)
        if not base.exists():
            return []
        found = []
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                whole = Path(dirpath) / name
                found.append(whole.relative_to(self._root).as_posix())
        return sorted(found)

    # -- writing ----------------------------------------------------------------------------
    def write_text(self, rel: str, content: str) -> None:
        """Every write is ATOMIC: the bytes go to a sibling temporary file, are flushed to the
        disk, and then REPLACE the target in one rename. A reader sees the old document or the
        new one and never a truncated one, and a process killed mid-write leaves the old document
        intact. Writing in place was honest to the WRITER and tearable for the READER -- the
        externalise-before-it-is-lost identity half-adopted, because a record nobody can read
        whole has not been externalised.

        The sibling shares the target's directory because a rename is atomic only within one
        filesystem. The residue is DECLARED, not hidden: a process killed between the write and
        the rename leaves a `.<name>.<pid>.kit-tmp` beside the target -- a visible stray the next
        reading names, instead of a silently torn document that reads as a real one."""
        norm = self._permit(rel)
        target = self._root / norm
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.kit-tmp")
        try:
            with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            _replace(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def write_tree(self, rel: str, files: dict) -> None:
        """Replace the DIRECTORY `rel` whole with exactly `files` (paths relative to it -> bytes,
        written verbatim). A tree is not a file, and writing it one file at a time would leave a
        reader -- or a run killed half-way -- a directory that is neither the old tree nor the new
        one: a mixture no record describes, which then reads exactly like a whole one.

        So the tree is STAGED in a sibling and SWAPPED in by rename, the way `write_text` swaps a
        document. The one honest difference is stated rather than hidden: a directory cannot be
        renamed over an existing one on every platform, so the swap is two renames -- the old tree
        aside, the new one in. A process killed between them leaves `.<name>.<pid>.kit-old` and no
        `<name>`: a visible, named residue that the next reading refuses, never a torn tree. Both
        sibling names are the port's own mechanism, exactly as the `.kit-tmp` of a document is."""
        norm = self._permit(rel)
        target = self._root / norm
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = target.with_name(f".{target.name}.{os.getpid()}.kit-tmp")
        aside = target.with_name(f".{target.name}.{os.getpid()}.kit-old")
        try:
            stage.mkdir(parents=True, exist_ok=True)
            for sub, content in files.items():
                dest = stage / _normalise(sub)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)
            if target.exists():
                _replace(target, aside)
            _replace(stage, target)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            if aside.exists() and not target.exists():
                _replace(aside, target)
            raise
        shutil.rmtree(aside, ignore_errors=True)

    def write_json(self, rel: str, value) -> None:
        self.write_text(rel, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def make_dir(self, rel: str) -> None:
        """A directory the host will fill. Declared and scope-checked like any other write: a
        space a capability owns is still a write scope, and an unowned one is how files appear
        that resolve to no class."""
        (self._root / self._permit(rel)).mkdir(parents=True, exist_ok=True)

    def relocate(self, source: str, destination: str) -> None:
        """Move ONE path -- a file, or a link as itself, never through it -- by a RENAME, never a
        copy and a delete: a rename is atomic within one filesystem, so a process killed at any
        instant leaves the path whole at exactly one of its two names, and never a torn copy
        beside an intact original. Both names are scope-checked. A destination that exists is
        REFUSED, never replaced (git's refusal to overwrite, Home-Manager's refusal to clobber);
        the check stands immediately before the rename, and on Windows the rename itself refuses
        an existing target. A rename across filesystems fails loudly rather than degrading into
        a copy (ADR-012)."""
        src = self._root / self._permit(source)
        dst = self._root / self._permit(destination)
        if os.path.lexists(dst):
            raise WriteScopeError(f"relocate refused: {destination!r} already exists")
        dst.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.rename(src, dst)
                return
            except PermissionError:
                if attempt == _REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(_REPLACE_PAUSE)

    def prune(self, rel: str, stop: str) -> list[str]:
        """Remove the directories from `rel` upward, never above `stop`, while each is EMPTY --
        and not one that is not: an empty directory is the shape a relocation left behind, and a
        directory holding anything is somebody's. Returns what was removed."""
        halt = _normalise(stop)
        removed = []
        current = PurePosixPath(_normalise(rel))
        while current.as_posix() == halt or current.as_posix().startswith(halt + "/"):
            whole = self._root / self._permit(current.as_posix())
            if not whole.is_dir() or os.path.islink(whole) or any(whole.iterdir()):
                break
            whole.rmdir()
            removed.append(current.as_posix())
            current = current.parent
        return removed

    def remove_file(self, rel: str) -> None:
        """Remove ONE file, scope-checked like every write. Additive (ADR-013): a projection
        outside the planes is removed one path at a time, because there is no tree of it to
        rebuild wholesale -- and the directories left empty are pruned up to its top segment,
        never one that still holds anything."""
        norm = self._permit(rel)
        target = self._root / norm
        if target.is_file():
            target.unlink()
            parent = PurePosixPath(norm).parent
            if parent.parts:
                self.unscoped().prune(parent.as_posix(), parent.parts[0])

    def remove_tree(self, rel: str) -> None:
        norm = self._permit(rel)
        target = self._root / norm
        if target.exists():
            shutil.rmtree(target)
