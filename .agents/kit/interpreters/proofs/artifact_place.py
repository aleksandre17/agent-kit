"""A reference to a PLACE in this host's tree: is the thing the criterion points at there?

The plainest kind of proof there is, and the one that shows most clearly why the third reading
exists. Present is a reading that was taken and held. Absent is NOT a refutation: nothing about
the work was measured, only that the referent this criterion names is not where it says it is --
which is as likely to be a moved file or a typed path as a promise unkept.

So this resolver never reports a failure. It reports what it saw, or that it saw nothing, and the
difference between those two is preserved all the way to the surface.
"""

from __future__ import annotations

import criteria


def _artifact_present(request) -> criteria.Verdict:
    if request.ctx.workspace.exists(request.ref):
        return criteria.Verdict(True, f"{request.ref} is in this host's tree")
    return criteria.Verdict.unreadable(
        f"nothing is at {request.ref} in this host's tree. A referent that is not there names "
        f"nothing -- which is not a claim that was tested and did not hold"
    )


RESOLVERS = {"artifact-present": _artifact_present}
