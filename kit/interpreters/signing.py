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

import re

import doors


def _walk(value, where: str):
    if isinstance(value, dict):
        yield where, value
        for key, inner in value.items():
            yield from _walk(inner, f"{where}.{key}" if where else key)
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _walk(inner, f"{where}[{index}]")


def marks(record) -> dict:
    """{(who, moment): the door it opens} -- every acceptance a record carries, wherever it stands in it:
    a door's passage or any acceptance (`signed_by`), a lowering (`approved_by`). A door walked twice
    is one door: its passages share a description, so one signed mark holds it."""
    found = {}
    for where, item in _walk(record, ""):
        if item.get(doors.SIGNED_BY):
            moment = str(item.get(doors.SIGNED_AT) or item.get("at") or "")
            door = f"the passage to {item['to']}" if item.get("to") else f"the acceptance at {where or 'the top'}"
            found[(str(item[doors.SIGNED_BY]), moment)] = door
        elif item.get("approved_by"):
            found[(str(item["approved_by"]), str(item.get("at") or ""))] = \
                f"the lowering to {item.get('to')} (from {item.get('from')})"
    return found


def reviews(record) -> dict:
    """{(reviewer, moment): what was judged} -- a review record's verdict, a name like any other: it
    is held to a signature only when the name is one an allowed signer signs as."""
    if isinstance(record, dict) and record.get("reviewer") and record.get("verdict"):
        return {(str(record["reviewer"]), str(record.get("at") or "")):
                f"the review of {record.get('card')} ({record['verdict']})"}
    return {}


def doors_of(card_marks: dict) -> dict:
    """{door: [(who, moment)]} -- the marks grouped by the door each opens."""
    grouped: dict = {}
    for key, door in card_marks.items():
        grouped.setdefault(door, []).append(key)
    return grouped


def principals(text: str, namespace: str = "git") -> list:
    """The principals an allowed-signers file lets sign in `namespace` (its first field, comma-separated),
    in order: a line restricted by `namespaces="..."` to others -- a capability publisher's -- is not one."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        restricted = re.search(r'namespaces="([^"]*)"', line)
        if restricted and namespace not in [n.strip() for n in restricted.group(1).split(",")]:
            continue
        out += [p for p in line.split()[0].split(",") if p and p not in out]
    return out


def trust_root(capabilities) -> "tuple | None":
    """(the host's trust root, the declared verifier's argv, the capability that seeds the root) -- read
    from the declared verifier (ADR-008), so a signature has one root and one program, named once."""
    for capability in capabilities:
        for doc in capability.documents.values():
            for verifier in (doc.get("verifiers") if isinstance(doc, dict) else None) or []:
                root = verifier.get("trust_root")
                owner = next((c for c in capabilities for i in c.installs if i.get("target") == root), None)
                if root and verifier.get("argv"):
                    return root, list(verifier["argv"]), owner
    return None


def signers_line(principal: str, public_key: str) -> str:
    """One allowed-signers line: the principal may sign git objects with this key, and nothing else."""
    return f'{principal} namespaces="git" {" ".join(public_key.split()[:2])}'
