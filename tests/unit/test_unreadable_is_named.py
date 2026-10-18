"""What cannot be read is named, never read as absent (CWE-223, CWE-636): a detector's JSON file that is
there and does not parse refuses the reading (KIT0093), and a ledger line that cannot be read is
counted -- a key on it is never reported as one that was "never measured"."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

INTERPRETERS = Path(__file__).resolve().parents[2] / "kit" / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import documents  # noqa: E402
import readings  # noqa: E402
from errors import EvidenceUnreadable  # noqa: E402


def test_a_json_file_that_is_there_and_does_not_parse_refuses_the_reading(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts": {"test": "jest",}}', encoding="utf-8")
    ws = SimpleNamespace(path=lambda rel: tmp_path / rel)
    with pytest.raises(EvidenceUnreadable, match="package.json is there and is not JSON"):
        documents._json_path(ws, {"path": "package.json", "pointer": "scripts.test"}, set())
    assert documents._json_path(ws, {"path": "absent.json", "pointer": "a"}, set()) == (False, None)


def test_a_ledger_line_that_cannot_be_read_is_counted_and_named_in_a_miss(monkeypatch):
    lines = "\n".join(['{"key": "kept", "ok": 1}', "not json", '{"key": "invalid"}'])
    ctx = SimpleNamespace(workspace=SimpleNamespace(exists=lambda _r: True, read_text=lambda _r: lines),
                          manifest=SimpleNamespace(validate=lambda row, _k: [] if row.get("ok") else ["invalid"]))
    monkeypatch.setattr(readings, "_place", lambda _ctx: ".agents/runtime/readings.jsonl")
    assert readings._read(ctx) == ({"kept": {"key": "kept", "ok": 1}}, 2)
    with pytest.raises(readings.GroundMiss, match="or it was, on one of the 2 ledger line"):
        readings.get(ctx, "lost")


def test_a_report_counter_that_does_not_parse_is_unreadable_never_zero_failures():
    import suite_report

    # A suite that lists no cases is read by its counting attributes -- one of which does not parse.
    report = b'<testsuite tests="3" failures="two" errors="0"/>'
    request = SimpleNamespace(ref="r.xml", ctx=SimpleNamespace(workspace=SimpleNamespace(
        exists=lambda _r: True, read_bytes=lambda _r: report)))
    verdict = suite_report._test_report_passed(request)
    assert verdict.holds is None and 'failures="two"> is not a count' in verdict.reading, verdict.reading


def test_a_peer_write_that_cannot_be_read_refuses_rather_than_admits(monkeypatch):
    import claims

    ctx = SimpleNamespace(workspace=SimpleNamespace(exists=lambda _r: True, files_under=lambda _b: ["w/peer.jsonl"],
                                                    read_text=lambda _r: '{"path": "a.py", "at": "2026-10-18T00:00:00Z"}\n{torn'))
    monkeypatch.setattr(claims, "_writes_place", lambda _ctx: "w")
    with pytest.raises(claims.PeerWriteUnreadable, match="w/peer.jsonl:2: a peer's recorded write cannot be read"):
        claims._peer_writes(ctx, ["me"])


def test_a_document_that_cannot_be_read_owes_an_unknown_never_nothing():
    import routes

    def unreadable(_rel):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    ctx = SimpleNamespace(workspace=SimpleNamespace(read_text=unreadable))
    assert routes._owed(ctx, SimpleNamespace(path="docs/a.md"), []) is None
    readable = SimpleNamespace(workspace=SimpleNamespace(read_text=lambda _r: "nothing owed\n"))
    assert routes._owed(readable, SimpleNamespace(path="docs/b.md"), []) == []


def test_every_line_a_law_page_holds_outside_its_numbered_laws_is_named():
    import laws

    page = "# Laws\n\nA preface nobody numbered.\n\n1. **One.** The first law.\n2. **Two.** The second.\n\n- a bulleted law\n"
    assert [n for n, *_ in laws.items(page)] == [1, 2]
    assert laws.outside(page) == ["# Laws", "A preface nobody numbered."]
    # What follows the last numbered law is carried INTO it, never dropped: it moves with that rule.
    assert "a bulleted law" in laws.items(page)[-1][2]
