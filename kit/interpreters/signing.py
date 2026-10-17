"""An owner's mark is a signature, not a name -- where the host declares it (ADR-025 amendment 3).

A door's acceptance is recorded as a NAME and a MOMENT (`doors.record`): a passage through a door
state (`signed_by`, `signed_at`), a lowering of a card's class (`approved_by`, `at`). A name is text,
and anything that can write the card can write it -- an agent included. Where a host declares
`owner_signing`, a mark counts only once a commit SIGNED by the key of the principal it names carries
it: git verifies the signature against the host's allowed-signers file (OpenSSH's format, git's own
`gpg.ssh.allowedSignersFile`); this module holds no key, reads no passphrase and verifies nothing
itself -- it says which marks a card holds and which door each one opens.

A door is held when ONE of its marks is signed: an unsigned mark beside a signed one opens nothing the
signed one did not, and a door whose only mark is unsigned is walked again in a commit the owner signs
-- history is never rewritten to repair it.
"""

from __future__ import annotations

import doors


def marks(card: dict) -> dict:
    """{(who, moment): the door it opens} -- every owner's mark the card records."""
    found = {}
    for passage in card.get("history") or []:
        if isinstance(passage, dict) and passage.get(doors.SIGNED_BY):
            found[(str(passage[doors.SIGNED_BY]), str(passage.get(doors.SIGNED_AT) or passage.get("at") or ""))] = \
                f"the passage to {passage.get('to')}"
    for entry in card.get("reshaped") or []:
        if isinstance(entry, dict) and entry.get("approved_by"):
            found[(str(entry["approved_by"]), str(entry.get("at") or ""))] = \
                f"the lowering to {entry.get('to')} (from {entry.get('from')})"
    return found


def doors_of(card_marks: dict) -> dict:
    """{door: [(who, moment)]} -- the marks grouped by the door each opens."""
    grouped: dict = {}
    for key, door in card_marks.items():
        grouped.setdefault(door, []).append(key)
    return grouped


def principals(text: str) -> list:
    """The principals an allowed-signers file names (its first field, comma-separated), in order."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out += [p for p in line.split()[0].split(",") if p and p not in out]
    return out


def signers_line(principal: str, public_key: str) -> str:
    """One allowed-signers line: the principal may sign git objects with this key, and nothing else."""
    return f'{principal} namespaces="git" {" ".join(public_key.split()[:2])}'
