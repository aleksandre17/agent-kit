"""Laws -- a host's served law list has ONE source: its numbered rules in the normative tree (ADR-024 d. 21).

A host used to hold its laws twice: as prose in a law page (served into every runtime's briefing) and as
structured rules in its norms (the normative tree `check` holds coherent). Two homes for one law agree
until one of them is edited. So a host rule may carry `law: <n>` -- its number in the served list -- and
an optional `enforcement_note`; the list is rendered from those rules in law order, and the page is
DEPRECATED: still served while it exists and no rule carries a number, refused by `check` once both
are authored, and moved into rules by `upgrade --mode laws`.

This module is pure: it reads a page's numbered items into rules, and judges a set of numbers. It
knows no path; the deprecated page's place arrives from the gate that declares it.
"""

from __future__ import annotations

import re

#: The field a numbered rule carries, and the note beside it -- the `cardinal` schema's words.
FIELD, NOTE = "law", "enforcement_note"
#: The contract a numbered rule keeps: the schema that declares those two words.
CONTRACT = "cardinal"
_ITEM = re.compile(r"^(\d+)\.[ \t]+(.*?)(?=^\d+\.[ \t]|\Z)", re.MULTILINE | re.DOTALL)
_TITLE = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.DOTALL)
#: A trailing emphasised sentence is where a law page names its enforcement.
_ENFORCED = re.compile(r"^(.*?)\s*(?<!\*)\*([^*][^*]*?)\*\s*$", re.DOTALL)
#: A seed's placeholder item, `_(none declared yet)_`, is not a law.
_PLACEHOLDER = re.compile(r"^_\(.*\)_$")


def items(text: str) -> list:
    """(number, title, says, enforcement note or None) for every numbered law the page holds."""
    found = []
    for match in _ITEM.finditer(text):
        body = " ".join(line.strip() for line in match.group(2).splitlines()).strip()
        if not body or _PLACEHOLDER.match(body):
            continue
        titled = _TITLE.match(body)
        title, rest = (titled.group(1).strip(), titled.group(2).strip()) if titled else ("", body)
        noted = _ENFORCED.match(rest)
        says, note = (noted.group(1).strip(), noted.group(2).strip()) if noted else (rest, None)
        found.append((int(match.group(1)), title or says.split(".")[0] + ".", says or title, note))
    return found


def outside(text: str) -> list:
    """Every non-blank line the page holds outside its numbered laws -- a heading, a preface, a law written
    in another form. Retiring the page removes them with it, so each is named first (CWE-223)."""
    covered = [match.span() for match in _ITEM.finditer(text)]
    found, at = [], 0
    for line in text.splitlines(keepends=True):
        if line.strip() and not any(start <= at < end for start, end in covered):
            found.append(line.strip())
        at += len(line)
    return found


def rules(text: str, address: str, publisher: str, genre: str, version: int) -> list:
    """The page's laws as host rules the host then completes (`derives_from`, `modality`, `subject`):
    `address` is the `<id>@<semver>` they are published under, `publisher` who moved them, `genre`
    the one the gate declares a law is, `version` the one the contract's schema states."""
    made = []
    for number, title, says, note in items(text):
        rule = {"schema_version": version, "id": f"{address}#law-{number}", "genre": genre, "title": title,
                "says": says, "publisher": publisher, FIELD: number}
        if note:
            rule[NOTE] = note
        made.append(rule)
    return made


def numbered(norms: list) -> list:
    """The norms that carry a law number, in the order they are declared."""
    return [n for n in norms if isinstance(n, dict) and FIELD in n]


def judged(page_present: bool, page: str, norms: list) -> list:
    """What makes the served law list ambiguous or out of order -- each named, never resolved."""
    failures = []
    numbers = [n[FIELD] for n in numbered(norms)]
    if page_present and numbers:
        failures.append(f"two sources for this host's laws: {page} and {len(numbers)} numbered rule(s) in "
                        f"its norms. Move what the page still says into rules and remove the page "
                        f"(`upgrade --mode laws` does both), so one source is in force")
    if numbers != list(range(1, len(numbers) + 1)):
        failures.append(f"the numbered rules carry laws {numbers}; the served list is in law order, so they "
                        f"are declared in that order and numbered 1..{len(numbers)} without a gap or a repeat")
    return failures
