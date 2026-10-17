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


def _junit(root) -> tuple:
    suites = [root] if _local(root.tag) == "testsuite" else [e for e in root if _local(e.tag) == "testsuite"]
    totals = [sum(_int(s, k) for s in suites) for k in ("tests", "failures", "errors")]
    if _local(root.tag) == "testsuites" and root.get("tests") is not None:
        totals = [_int(root, k) for k in ("tests", "failures", "errors")]
    return tuple(totals)


def _trx(root) -> tuple:
    counters = next((e for e in root.iter() if _local(e.tag) == "Counters"), None)
    if counters is None:
        return 0, 0, 0
    return _int(counters, "total"), _int(counters, "failed"), _int(counters, "error") + _int(counters, "aborted")


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
    if total == 0:
        return criteria.Verdict.unreadable(f"{ref} counts no test: a run that ran nothing proves nothing")
    if failed or errored:
        return criteria.Verdict(False, f"{ref}: {failed} failed and {errored} errored of {total}")
    return criteria.Verdict(True, f"{ref}: {total} test(s), none failed")


RESOLVERS = {"test-report-passed": _test_report_passed}
