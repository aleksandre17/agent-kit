"""A plane is written by its writer -- an interactive session's hand edit inside one is refused.

The pinned kit (`vendor`) is replaced wholesale by `upgrade` and judged against its lock; the
generated plane (`projection`) is rebuilt from scratch by `render` and judged byte for byte. Both are
already caught by `check` AFTER the fact. This kind refuses the edit BEFORE it lands, for the
writers a host's gate names by runtime CLASS (an interactive session, typically): that session has a
verb to run instead, and a hand edit there is work the next render or upgrade silently discards.

A batch writer -- a commit, a CI run -- is not refused here: it carries whatever the plane's own
writer wrote (an upgrade's new kit), and `check` is what judges that tree. Where the writer is not
known (the judge was not told which runtime is writing), the edit is judged as if it were one of
the named writers: an unknown writer is not an exempt one.
"""

from __future__ import annotations

KIND = "plane-held-by-its-writer"


def _roots(ctx, params) -> list:
    return [(p["root"].rstrip("/") + "/", p["class"]) for p in ctx.manifest.planes
            if p["class"] in params["classes"]]


def _held(ctx, params):
    """The declaration is believed only if every class it names is a plane this kit declares."""
    declared = {p["class"] for p in ctx.manifest.planes}
    return [f"{KIND}: names the plane class {c!r}, which this kit declares no plane of -- the gate "
            f"would refuse nothing it claims to" for c in params["classes"] if c not in declared]


def _judged(ctx, params, edits):
    writers = getattr(ctx, "writers", None)
    if writers and not set(writers) & set(params["writers"]):
        return [], []
    refused = []
    for path, _text in edits:
        for root, klass in _roots(ctx, params):
            if path.startswith(root):
                refused.append((path, KIND, f"{root} is the {klass} plane, written only by "
                                f"its own verb; a hand edit there is discarded by the next one.",
                                params["instead"][klass]))
    return refused, []


KINDS = {KIND: _held}
EDITS = {KIND: _judged}
