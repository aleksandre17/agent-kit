"""A claim never exceeds its evidence: a criterion that needs a class is proved only by a reading worth
it (ADR-025 decision 7), and the two evidence-bearing kinds of proof read what they say they read."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

KIT = Path(__file__).resolve().parents[2] / "kit"
for extra in (KIT / "interpreters", KIT / "interpreters" / "proofs"):
    sys.path.insert(0, str(extra))

import criteria  # noqa: E402
import review_record  # noqa: E402
import suite_report  # noqa: E402

SCALE = json.loads((KIT / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))["evidence"]
HELD = criteria.Verdict(True, "it held")


def needs(kind, want):
    return criteria.needed(SCALE, {"id": "c", "needs": want, "proof": {"kind": kind, "ref": "x"}}, HELD)


def test_a_stronger_rung_satisfies_a_weaker_need_and_never_the_reverse():
    assert needs("test-report-passed", "static").holds is True
    assert needs("artifact-present", "tested").holds is None


def test_a_judgement_satisfies_only_itself():
    assert needs("review-approved", "review").holds is True
    assert needs("test-report-passed", "review").holds is None
    assert needs("review-approved", "tested").holds is None


def test_a_composite_kind_yields_no_class_of_its_own():
    assert needs("criteria-all-hold", "static").holds is None


def test_no_need_and_no_hold_pass_through_untouched():
    assert criteria.needed(SCALE, {"proof": {"kind": "artifact-present"}}, HELD) is HELD
    refuted = criteria.Verdict(False, "no")
    assert criteria.needed(SCALE, {"needs": "tested", "proof": {"kind": "x"}}, refuted) is refuted


def test_one_kind_worth_two_classes_is_refused():
    with pytest.raises(criteria.CriterionError):
        criteria.evidence(SCALE + [{"id": "dup", "says": "x", "ladder": False, "yielded_by": ["artifact-present"]}])


# -- the two kinds of proof that carry evidence --------------------------------------------------
class Tree:
    def __init__(self, files: dict) -> None:
        self.files = files

    def exists(self, rel):
        return rel in self.files

    def read_text(self, rel):
        return self.files[rel]

    def read_bytes(self, rel):
        return self.files[rel].encode("utf-8")


def request(files, ref, subject=None, schema_errors=()):
    ctx = SimpleNamespace(workspace=Tree(files), manifest=SimpleNamespace(validate=lambda *_: list(schema_errors)))
    return SimpleNamespace(ctx=ctx, ref=ref, subject=subject or {"id": "orders", "owner": "dev"})


JUNIT = '<testsuites tests="3" failures="0" errors="0"><testsuite tests="3"/></testsuites>'
TRX = ('<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010"><ResultSummary>'
       '<Counters total="37" passed="37" failed="0" error="0" aborted="0"/></ResultSummary></TestRun>')


def test_a_passing_junit_or_trx_report_holds():
    assert suite_report._test_report_passed(request({"r.xml": JUNIT}, "r.xml")).holds is True
    assert suite_report._test_report_passed(request({"r.trx": TRX}, "r.trx")).holds is True


def test_a_failing_report_is_refuted_and_an_empty_or_foreign_one_proves_nothing():
    failing = '<testsuite tests="2" failures="1" errors="0"/>'
    assert suite_report._test_report_passed(request({"r.xml": failing}, "r.xml")).holds is False
    assert suite_report._test_report_passed(request({"r.xml": '<testsuite tests="0"/>'}, "r.xml")).holds is None
    assert suite_report._test_report_passed(request({"r.xml": "<html/>"}, "r.xml")).holds is None
    assert suite_report._test_report_passed(request({}, "r.xml")).holds is None


def review(reviewer, verdict="approved", card="orders"):
    return json.dumps({"schema_version": 1, "card": card, "reviewer": reviewer, "verdict": verdict,
                       "reviewed": "abc123", "at": "2026-10-17"})


def test_an_approval_by_someone_else_holds_and_changes_requested_is_refuted():
    assert review_record._review_approved(request({"r.json": review("peer")}, "r.json")).holds is True
    assert review_record._review_approved(request({"r.json": review("peer", "changes-requested")}, "r.json")).holds is False


def test_a_review_by_an_author_or_of_another_card_proves_nothing():
    mover = {"id": "orders", "owner": "dev", "history": [{"from": "a", "to": "b", "at": "t", "by": "agent"}]}
    assert review_record._review_approved(request({"r.json": review("dev")}, "r.json")).holds is None
    assert review_record._review_approved(request({"r.json": review("agent")}, "r.json", mover)).holds is None
    assert review_record._review_approved(request({"r.json": review("peer", card="other")}, "r.json")).holds is None
    assert review_record._review_approved(request({"r.json": review("peer")}, "r.json", schema_errors=["bad"])).holds is None


def test_a_report_where_every_test_was_skipped_proves_nothing():
    skipped = '<testsuite tests="4" failures="0" errors="0" skipped="4"/>'
    assert suite_report._test_report_passed(request({"r.xml": skipped}, "r.xml")).holds is None
    trx = ('<TestRun><ResultSummary><Counters total="4" executed="0" passed="0" failed="0" error="0"/>'
           '</ResultSummary></TestRun>')
    assert suite_report._test_report_passed(request({"r.trx": trx}, "r.trx")).holds is None


def test_the_owner_who_walked_the_door_may_still_review():
    bet = {"id": "orders", "owner": "dev",
           "history": [{"from": "shaped", "to": "bet", "at": "t", "by": "owner", "signed_by": "owner"},
                       {"from": "bet", "to": "in-flight", "at": "t", "by": "dev"}]}
    assert review_record._review_approved(request({"r.json": review("owner")}, "r.json", bet)).holds is True
    assert review_record._review_approved(request({"r.json": review("dev")}, "r.json", bet)).holds is None


def test_whoever_carried_a_card_through_a_door_is_still_its_author():
    # Found by an audit: `move --by agent --approve owner` exempted the agent from authorship.
    carried = {"id": "orders", "owner": "dev",
               "history": [{"from": "shaped", "to": "bet", "at": "t", "by": "agent", "signed_by": "owner"}]}
    assert review_record._review_approved(request({"r.json": review("agent")}, "r.json", carried)).holds is None
    assert review_record._review_approved(request({"r.json": review("owner")}, "r.json", carried)).holds is True


def test_a_root_that_says_nothing_of_skips_never_outvotes_children_that_skipped_everything():
    jest = '<testsuites tests="5" failures="0" errors="0"><testsuite tests="5" skipped="5"/></testsuites>'
    assert suite_report._test_report_passed(request({"r.xml": jest}, "r.xml")).holds is None
    cases = ('<testsuite tests="3" failures="0" errors="0">'
             + '<testcase name="a"><skipped/></testcase>' * 3 + '</testsuite>')
    assert suite_report._test_report_passed(request({"r.xml": cases}, "r.xml")).holds is None
    failed = ('<testsuite tests="2" failures="0" errors="0"><testcase name="a"/>'
              '<testcase name="b"><failure message="x"/></testcase></testsuite>')
    assert suite_report._test_report_passed(request({"r.xml": failed}, "r.xml")).holds is False


def test_a_trx_run_holds_only_when_every_executed_test_passed():
    timed_out = ('<TestRun><ResultSummary><Counters total="5" executed="5" passed="0" failed="0" error="0" '
                 'timeout="5"/></ResultSummary></TestRun>')
    assert suite_report._test_report_passed(request({"r.trx": timed_out}, "r.trx")).holds is False
    inconclusive = ('<TestRun><ResultSummary><Counters total="5" executed="5" passed="3" failed="0" error="0" '
                    'inconclusive="2"/></ResultSummary></TestRun>')
    assert suite_report._test_report_passed(request({"r.trx": inconclusive}, "r.trx")).holds is False
