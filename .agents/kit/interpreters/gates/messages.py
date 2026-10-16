"""Message rules -- a host's judgement over the message a change is recorded with, calibrated like an
edit gate (ADR-024 decision 17).

This module knows no rule, no convention and no product. It knows one SHAPE: a pattern a message must
match, why, what instead, and the rule's own calibration -- one message it must refuse, one it must
admit. Which rules exist is every document an enabled capability keeps under the contract this gate
kind is declared over, so `check` (which calibrates) and the `message` verb (which applies) read one
declaration and cannot disagree.
"""

from __future__ import annotations

import re

import declared

#: The field by which a message-rules document carries its rows -- the schema's word, one home.
RULES = "rules"
KIND = "message-rules-calibrated"
#: Git's default comment character, and the line below which `commit -v` puts the diff.
COMMENT, SCISSORS = "#", re.compile(r"^# -+ >8 -+$", re.MULTILINE)


def cleaned(message: str) -> str:
    """The message as it will be recorded: everything below a scissors line and every comment line
    removed, surrounding blank lines dropped."""
    cut = SCISSORS.search(message)
    message = message[:cut.start()] if cut else message
    return "\n".join(line for line in message.splitlines() if not line.startswith(COMMENT)).strip()


def _pattern(rule):
    try:
        return re.compile(rule["requires"], re.MULTILINE), None
    except re.error as exc:
        return None, f"{rule['id']}: its requires {rule['requires']!r} is not a pattern -- {exc}"


def refuses(rule, message: str) -> bool:
    pattern, _ = _pattern(rule)
    return bool(pattern) and not pattern.match(cleaned(message))


def calibration(rule) -> list:
    """What a rule can prove about itself before any message is judged on its word."""
    _, broken = _pattern(rule)
    if broken:
        return [broken]
    failures = []
    if not refuses(rule, rule["proves"]):
        failures.append(f"{rule['id']}: UNCALIBRATED -- it admits the message it declares it refuses "
                        f"({rule['proves']!r}). No message is judged on its word.")
    if refuses(rule, rule["admits"]):
        failures.append(f"{rule['id']}: UNCALIBRATED -- it refuses the message it declares legitimate "
                        f"({rule['admits']!r}). No message is judged on its word.")
    return failures


def judge(rules: list, message: str) -> tuple:
    """(refusing rules, unjudged rule ids): every calibrated rule the message breaks, and every rule that
    could not be applied because it is uncalibrated -- named, never silently skipped and never trusted."""
    calibrated = [rule for rule in rules if not calibration(rule)]
    unjudged = [rule["id"] for rule in rules if calibration(rule)]
    return [rule for rule in calibrated if refuses(rule, message)], unjudged


def _message_rules_calibrated(ctx, params):
    return [failure for rule in declared.rules(ctx, params["sources"], RULES) for failure in calibration(rule)]


def _calibrate(host):
    """A rule that admits its own specimen is flagged; one that refuses it and admits its lookalike is not."""
    good = {"id": "r", "requires": "^ok", "because": "b", "instead": "i", "proves": "no", "admits": "ok"}
    return calibration({**good, "proves": "ok then"}), calibration(good)


KINDS = {KIND: _message_rules_calibrated}
CALIBRATIONS = {KIND: _calibrate}
