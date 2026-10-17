"""A reference to a TEST REPORT kept as evidence: did the suite it records run, and fail nothing?

ADR-025 decision 7. A test is evidence only if it ran and its report was kept: a claim that tests
pass, typed anywhere, is testimony. This resolver reads the two report formats suites write as a
matter of course -- JUnit XML (`<testsuites>` / `<testsuite>`, the de facto interchange format) and
the Visual Studio TRX (`<TestRun>`, what `dotnet test --logger trx` writes) -- and holds only when the
report counts at least one test and no failure and no error. A report that counts nothing proves
nothing: an empty run passes gloriously and reads exactly like a run that looked.

The XML is read with the standard library's parser, which resolves no external entity.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree

import criteria


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _int(element, name: str) -> int:
    try:
        return int(float(element.get(name, "0") or 0))
    except ValueError:
        return 0


def _suite(suite) -> tuple:
    """(ran, failed, errored) of one suite: its test cases where it lists them -- a case with a
    <skipped/> did not run -- else its counting attributes."""
    cases = [e for e in suite if _local(e.tag) == "testcase"]
    if cases:
        marks = [{_local(x.tag) for x in case} for case in cases]
        return (sum(1 for m in marks if "skipped" not in m), sum(1 for m in marks if "failure" in m),
                sum(1 for m in marks if "error" in m))
    return _int(suite, "tests") - _int(suite, "skipped"), _int(suite, "failures"), _int(suite, "errors")


def _junit(root) -> tuple:
    """(ran, failed, errored), read the way that proves the least: the suites summed, and a root's own
    totals only ever LOWER what ran or RAISE what failed -- a root that counts tests and says nothing of
    the skipped (jest-junit's) never outvotes children that say all of them were."""
    suites = [root] if _local(root.tag) == "testsuite" else [e for e in root if _local(e.tag) == "testsuite"]
    ran, failed, errored = (sum(column) for column in zip(*[_suite(s) for s in suites])) if suites else (0, 0, 0)
    if _local(root.tag) == "testsuites" and root.get("tests") is not None:
        skipped = _int(root, "skipped") if root.get("skipped") is not None else _int(root, "tests") - ran
        ran = min(ran, _int(root, "tests") - skipped) if suites else _int(root, "tests") - skipped
        failed, errored = max(failed, _int(root, "failures")), max(errored, _int(root, "errors"))
    return ran, failed, errored  # a skipped test was not run, and proves nothing


def _trx(root) -> tuple:
    """(executed, not passed, errored): a TRX run holds only where every executed test PASSED -- a
    timeout, an inconclusive or a not-executed-yet-counted test is not a pass."""
    counters = next((e for e in root.iter() if _local(e.tag) == "Counters"), None)
    if counters is None:
        return 0, 0, 0
    executed = _int(counters, "executed") if counters.get("executed") is not None else _int(counters, "total")
    errored = _int(counters, "error") + _int(counters, "aborted") + _int(counters, "timeout")
    failed = _int(counters, "failed")
    if counters.get("passed") is not None:
        failed = max(failed, executed - _int(counters, "passed") - errored)
    return executed, failed, errored


READERS = {"testsuites": _junit, "testsuite": _junit, "TestRun": _trx}


def _test_report_passed(request) -> criteria.Verdict:
    ctx, ref = request.ctx, request.ref
    if not ctx.workspace.exists(ref):
        return criteria.Verdict.unreadable(f"no test report is at {ref}")
    try:
        root = ElementTree.fromstring(ctx.workspace.read_bytes(ref))
    except ElementTree.ParseError as exc:
        return criteria.Verdict.unreadable(f"{ref} is not readable XML -- {exc}")
    reader = READERS.get(_local(root.tag))
    if reader is None:
        return criteria.Verdict.unreadable(f"{ref} is a <{_local(root.tag)}> document, which is neither a "
                                           f"JUnit nor a TRX report")
    total, failed, errored = reader(root)
    if total <= 0:
        return criteria.Verdict.unreadable(f"{ref} counts no test that ran: a run that ran nothing proves nothing")
    if failed or errored:
        return criteria.Verdict(False, f"{ref}: {failed} failed and {errored} errored of {total}")
    return criteria.Verdict(True, f"{ref}: {total} test(s), none failed")


RESOLVERS = {"test-report-passed": _test_report_passed}
