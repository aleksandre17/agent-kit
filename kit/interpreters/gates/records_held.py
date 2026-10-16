"""Gate kind for change records: every record is well formed and not stale, on every `check` (ADR-024).
Coverage over a review range is the `review` verb's, where the range is known."""

from __future__ import annotations

import changes

KIND = "change-records-held"


def _held(ctx, params) -> list:
    report = changes.validate(ctx)
    print(f"        READ {len(changes.records(ctx))} change record(s); change coverage {report['change_coverage']} "
          f"(a review range is read by `review`); runtime conformance {report['runtime_conformance']}")
    return report["errors"]


KINDS = {KIND: _held}
