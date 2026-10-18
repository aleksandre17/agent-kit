"""Unit: the declared-stopgaps policy refuses a stopgap comment tag that names no tracking record on its
line, and admits one that does -- and admits prose and code that only use the words (engineering 1.2.0,
a-stopgap-is-declared-debt)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE = json.loads((ROOT / "policies" / "declared-stopgaps" / "payload" / "edit-gates.json")
                  .read_text(encoding="utf-8"))["gates"][0]
FORBIDS = re.compile(GATE["forbids"], re.MULTILINE)


@pytest.mark.parametrize("line", [
    "// HACK: skip certificate validation until the server is upgraded",
    "# WORKAROUND: the vendor API returns 200 on failure",
    "    /* TEMPORARY: admit TLS 1.0 */",
    "-- STOPGAP (until the migration): read the old column",
    "// FIXME: this leaks a connection",
    "# XXX: remove before release",
])
def test_an_untracked_stopgap_is_refused(line):
    assert FORBIDS.search(line), line


@pytest.mark.parametrize("line", [
    "# TEMPORARY (AIR-019): admit TLS 1.0 until the DBA enables TLS 1.2",
    "// HACK: JIRA-4521 the vendor sends 200 on failure",
    "// WORKAROUND: #312 the SDK leaks a socket",
    "// STOPGAP: card: air-019-sql-server-tls-1-2",
    "CREATE TEMPORARY TABLE t (id int);",            # code, not a tag
    "A temporary workaround is debt; a hack is not a solution.",  # prose
    "var temporaryFile = Path.GetTempFileName();",
    "phone = 'XXX-XXX-XXXX'",
])
def test_a_tracked_stopgap_and_mere_words_are_admitted(line):
    assert not FORBIDS.search(line), line


def test_the_gate_holds_its_own_calibration_and_one_line_at_a_time():
    assert FORBIDS.search(GATE["proves"]["text"]) and not FORBIDS.search(GATE["admits"]["text"])
    # a tracking record on another line does not vouch for this one
    assert FORBIDS.search("// see AIR-019\n// HACK: no record on this line")


def test_the_rule_the_gate_enforces_names_it():
    norms = json.loads((ROOT / "bundles" / "engineering" / "payload" / "norms.json").read_text(encoding="utf-8"))
    rule = next(r for r in norms if r["id"].endswith("#a-stopgap-is-declared-debt"))
    assert rule["modality"] == "MUST" and f"edit-gate:{GATE['id']}" in rule["enforced_by"]
