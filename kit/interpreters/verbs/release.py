"""release -- state what this kit IS as a release, or refuse to call a working tree one (ADR-016).

A release is a kit whose bytes equal its own lock; its identity is the digest of that lock. This
verb is the one surface an author asks before a revision is tagged, and the one a host asks of the
kit it is running: it prints the version, the full lock digest, the number of paths the lock
enumerates, and -- every time -- that authenticity is NOT ESTABLISHED, because the kit's own lock
carries no signature yet. It writes nothing. A working tree is refused by name: a flag, a tag or a
sentence that called it a release would be the surface lying.

    python kit/interpreters/cli.py release --root <any repo>
    python .agents/kit/pinned/interpreters/cli.py release --root .     # what does this host run?

The subject is the KIT the interpreter was started from (`--kit`), never the host `--root` names.
"""

from __future__ import annotations

import pin

SUMMARY = "state what this kit is as a release, or refuse to call a working tree one"
MUTATES = False
#: What this verb reads is the KIT, never the host -- declared, as `lock` declares it (ADR-007).
SUBJECT = "kit"
REQUIRES_APPROVED_HOST = False


def run(ctx, args) -> int:
    seen = pin.reading(ctx.manifest)
    print(f"release: {ctx.manifest.root.as_posix()}")
    if not seen["released"]:
        named = ([f"{row['path']} ({row['state']})" for row in seen["unresolved"]]
                 + [f"{path} ({state})" for state, path, _why in seen["drift"]])
        raise pin.ReleaseError(
            f"{pin.identity(ctx.manifest)}"
            + (f" -- " + ", ".join(named[:8]) + (" ..." if len(named) > 8 else "") if named else "")
            + ". Take the lock (`lock`) upstream once the tree is what you mean to release")
    print(f"  {pin.identity(ctx.manifest)}")
    print(f"  {len(seen['rows'])} path(s), each digested in {seen['lock_path']}, read at "
          f"{seen['recorded']['taken_at']}")
    return 0
