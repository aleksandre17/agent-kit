"""A product that reads its hook's DECISION on stdout gets that decision and nothing else.

Most products refuse a tool call by the hook's exit code; others read a decision the hook writes to
stdout. A surface declares which (`hands.refusal.stdout`, `hands.admission.stdout`), and the judge
then writes every line of its own to stderr, so nothing but the declared decision is read as one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import judge  # noqa: E402


def test_a_stdout_decision_is_the_only_thing_on_stdout(capsys):
    say, refuse, admit = judge._speaker({
        "refusal": {"exit": 0, "stdout": '{"permission": "deny", "reason": "{reason}"}'},
        "admission": {"stdout": '{"permission": "allow"}'}})
    say("judge: a line of the judge's own")
    assert refuse('judge: REFUSED  a.ts  rule -- a "quoted" reason') == 0
    out, err = capsys.readouterr()
    assert json.loads(out) == {"permission": "deny", "reason": 'judge: REFUSED  a.ts  rule -- a "quoted" reason'}
    assert "a line of the judge's own" in err and "REFUSED" in err
    assert admit("judge: 1 edited path(s) pass") == 0
    out, err = capsys.readouterr()
    assert json.loads(out) == {"permission": "allow"} and "pass" in err


def test_an_exit_code_product_keeps_its_exit_and_its_stdout(capsys):
    say, refuse, admit = judge._speaker({"refusal": {"exit": 2}})
    say("judge: a line")
    assert refuse("judge: REFUSED  a.ts") == 2
    assert admit("judge: 1 edited path(s) pass") == 0
    out, err = capsys.readouterr()
    assert "a line" in out and "pass" in out and "REFUSED" in err and "REFUSED" not in out
