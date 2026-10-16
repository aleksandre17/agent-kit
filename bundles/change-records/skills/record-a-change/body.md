# Record a change

**Before editing.** Capture the baseline (`git rev-parse HEAD`, `git status --porcelain`, the known failures).
Search for an existing owner before creating anything. Open ONE record in the change-records space, status
OPEN: the files it will own, and APPLY or NA -- with a reason -- for every catalogued requirement. Do not
absorb unrelated dirty files.

**While editing.** Choose the evidence by risk (a rule: fixed-fixture regression; a schema: migration on a copy
plus a rollback note; an endpoint: unauthorised, wrong scope, allowed; a workflow: duplicate and concurrent;
an adapter: dependency down). A mock isolates a dependency and proves nothing about it. A test not run is
recorded NOT_RUN.

**Closing.** Run this skill's `scripts/digests.py <file>...` and paste its output as `source_digests` and the
evidence `sha256`; set VERIFIED only with every test's exit code 0. A later change to a covered file supersedes
the record (`superseded_by`); old evidence is never rewritten. `check` holds every record; `review --base
--head` holds the range.
