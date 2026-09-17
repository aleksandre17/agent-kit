"""PROVENANCE -- what a host TOOK that this kit did not issue, pinned at the door that took it.

The kit states what it IS in its lock, and a host states what it was GIVEN in its estate. Neither
says anything about a capability that arrived from somebody else -- a doctrine bundle a company
publishes, a capability one team wrote for itself. Until this module, such a thing was a
declaration a human had placed in a kit, and nothing recorded where it came from or could tell
the bytes its publisher released from bytes that were changed on the way (ADR-008).

Two layers, kept structurally apart because they are different propositions:

  * INTEGRITY -- a content digest of the capability, taken at FIRST CONTACT and pinned in the
    host's estate beside the name of the human who walked the door and the moment they did. Any
    later reading that disagrees with the pin is REFUSED and never re-pinned: a digest that could
    be quietly re-taken would pin nothing. This is `go.sum`, Subresource Integrity and
    `Cargo.lock` -- trust on first use, made a recorded act rather than an accident.
  * AUTHENTICITY -- whether the pinned bytes are the ones their publisher signed. The standard
    library has no asymmetric primitive and this kit hand-rolls no cryptography, so verification
    is DELEGATED to a verifier the kit declares as data (a registry row: argv, namespace, where
    the host keeps its trust root) and the publisher names in its claim. Where it could not run
    -- no claim, no trust root, no verifier on this machine -- the pin says so in a declared word.
    A verification that did not run is not a verification, and it is never printed as one.

What this module decides is only what can be MEASURED: which capabilities the kit's own lock
does not account for, what their bytes digest to, how a version compares with a pinned one, and
what a verifier's exit code was. What each measured state MEANS -- held, a door, a refusal -- is
read from `provenance.json`, and a state that document does not answer is refused rather than
defaulted. No publisher, key, verifier or capability is named here.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess

import doors
import estate as estate_module
import lockfile
import pin
import version_range
from errors import KitError
from workspace import Workspace

#: The id under which a capability ships the provenance declaration.
DOCUMENT = "provenance"

#: The states a taken capability can be MEASURED in. The words are the document's; these are the
#: measurements this module knows how to take, and each must be answered there.
PINNED = "pinned"
FIRST_CONTACT = "first-contact"
ADVANCED = "advanced"
DRIFTED = "drifted"
ROLLED_BACK = "rolled-back"
WITHDRAWN = "withdrawn"

#: What a state's disposition may be -- the effects this interpreter can carry out, one home.
HOLD, CARRY, DOOR, REFUSE = "hold", "carry", "door", "refuse"
DISPOSITIONS = (HOLD, CARRY, DOOR, REFUSE)

#: What an attempt at authenticity can measure.
VERIFIED = "signature-verified"
REFUTED = "signature-refuted"
UNSIGNED = "unsigned"
SIGNATURE_MISSING = "signature-missing"
UNKNOWN_VERIFIER = "unknown-verifier"
NO_TRUST_ROOT = "no-trust-root"
VERIFIER_ABSENT = "verifier-absent"
NOT_YET_READ = "not-yet-read"

#: How a pin stands (ADR-018 amendment 2): written at arrival on first use, or attested since.
TRUST_ON_FIRST_USE = "trust-on-first-use"
ATTESTED = "attested"


def unattested(pin) -> bool:
    return bool(pin) and (pin.get("trust") or {}).get("basis") == TRUST_ON_FIRST_USE


def arrival(capability: str, version: str, measured: str, who: str, when: str, prior=None) -> dict:
    """The pin a take writes AT ARRIVAL (ADR-018 amendment 2), marked trust-on-first-use: the
    digest of what arrived, so that nothing between the take and its attestation is admitted
    silently. A prior pin is judged first: bytes that differ at the same version, or an older
    version, are refused -- a take never re-pins a drift or walks a rollback."""
    if prior:
        now, then = (version_range.parse_version(v) for v in (version, prior["version"]))
        if now < then or (now == then and prior["digest"] != measured):
            raise ProvenanceRefused(
                f"{capability}@{version} {measured} would replace the pin {prior['version']} "
                f"{prior['digest']} (pinned by {prior['pinned_by']} at {prior['pinned_at']}); "
                f"a take never re-pins changed bytes or an older version")
        if now == then:
            return prior
    pin = {"capability": capability, "version": version, "digest": measured,
           "pinned_by": who, "pinned_at": when,
           "trust": {"basis": TRUST_ON_FIRST_USE},
           "authenticity": {"state": NOT_YET_READ, "taken_at": when}}
    if prior:
        pin["supersedes"] = {"version": prior["version"], "digest": prior["digest"]}
    return pin

#: The field of a capability declaration in which a publisher CLAIMS a signature. A claim, and
#: never proof: it names what to check, and establishes nothing until something checked it.
CLAIM = "provenance"


class ProvenanceRefused(KitError):
    """A capability this kit did not issue is not the bytes its host pinned, is older than the
    version pinned, or carries a signature its declared verifier refuted."""

    code = "KIT0032"


def declaration(ctx) -> dict:
    """The one provenance declaration this kit ships, or a refusal. Two would be two answers to
    what a drift means; none means a taken capability could only be defaulted, which is refused."""
    found = [c.documents[DOCUMENT] for c in ctx.manifest.capabilities if DOCUMENT in c.documents]
    if len(found) != 1:
        raise ProvenanceRefused(
            f"this kit ships {len(found)} provenance declarations; exactly one is required, "
            f"because a taken capability's state has exactly one meaning"
        )
    return found[0]


def _row(rows: list, key: str, word: str, what: str) -> dict:
    for row in rows:
        if row[key] == word:
            return row
    raise ProvenanceRefused(
        f"the provenance declaration says nothing about the {what} {word!r}. It was measured and "
        f"has no declared meaning, and a meaning supplied here would be a rule nobody declared"
    )


def disposition(ctx, state: str) -> str:
    return _row(declaration(ctx)["states"], "state", state, "state")["disposition"]


def _issued(ctx) -> set:
    """Every path the kit's own lock accounts for. The lock is the kit's reading of ITSELF; a
    capability whose declaration is not in it was not issued by this kit, and that is MEASURED
    against the lock rather than claimed by the capability."""
    path = pin.lock_file(ctx.manifest)
    if not path.is_file():
        raise ProvenanceRefused(
            f"{path.as_posix()}: this kit has no reading of itself, so nothing can tell a capability it "
            f"issued from one a host took from elsewhere. Take the kit's lock, then run again"
        )
    return lockfile.issued(json.loads(path.read_text(encoding="utf-8")))


def taken(ctx, capabilities) -> list:
    issued = _issued(ctx)
    return [c for c in capabilities if ctx.manifest.declaration_of(c.id) not in issued]


def h1(lines: list) -> str:
    """Go's `h1:` dirhash over already-measured `(path, bytes)` pairs: sha256 over the sorted lines
    `<sha256 of a file>  <path>`, base64. The one spelling of the algorithm (ADR-008)."""
    text = "".join(f"{hashlib.sha256(data).hexdigest()}  {rel}\n" for rel, data in sorted(lines))
    return "h1:" + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")


def tree_digest(home, prefix: str, signature=None) -> str:
    """The digest of a TAKEN capability: every file of its plane, spelled in the kit namespace its
    declaration uses (ADR-018 decision 3). The whole copied tree, never the closure of its
    declaration -- a file planted beside a take is part of what the host is running."""
    files = [(prefix + p.relative_to(home).as_posix(), p) for p in home.rglob("*") if p.is_file()]
    return h1([(rel, p.read_bytes()) for rel, p in files if rel != signature])


def digest(ctx, capability, issued=None) -> str:
    """The content digest of one capability: Go's `h1:` dirhash, adopted whole -- sha256 over the
    sorted lines `<sha256 of a file>  <path>`, base64. Its files are the closure of its
    declaration by the kit's one walker, less what the kit issued (the kit pins those) and less
    the signature its publisher claims (a digest cannot contain the signature over itself)."""
    take = ctx.manifest.take_of(capability.id)
    if take is not None:
        return tree_digest(take[0], take[1], (capability.raw.get(CLAIM) or {}).get("signature"))
    kit = Workspace(ctx.manifest.root)
    issued = _issued(ctx) if issued is None else issued
    skip = set(issued) | {ctx.manifest.raw_ships()["lock"]}
    signature = (capability.raw.get(CLAIM) or {}).get("signature")
    if signature:
        skip.add(signature)
    files = lockfile.closure(kit, ctx.manifest.declaration_of(capability.id), skip)
    return h1([(rel, kit.read_bytes(rel)) for rel in files])


def survey(ctx, capabilities, pins) -> list:
    """Every taken capability against the pin its host holds, and every pin whose capability is
    no longer taken. A pin outlives its capability on purpose: a pin that vanished with it would
    let a capability be removed and taken back at an OLDER version as though met for the first
    time -- the rollback, walked round rather than through."""
    held = {pin["capability"]: pin for pin in pins or []}
    issued = _issued(ctx)
    rows = []
    for capability in taken(ctx, capabilities):
        measured = digest(ctx, capability, issued)
        pin = held.pop(capability.id, None)
        if pin is None:
            state = FIRST_CONTACT
        else:
            now, then = (version_range.parse_version(v) for v in (capability.version, pin["version"]))
            order = (now > then) - (now < then)
            state = (ROLLED_BACK if order < 0 else ADVANCED if order > 0
                     else PINNED if pin["digest"] == measured else DRIFTED)
        rows.append({"capability": capability.id, "version": capability.version,
                     "digest": measured, "state": state, "pin": pin, "declared": capability})
    for pin in held.values():
        rows.append({"capability": pin["capability"], "version": pin["version"],
                     "digest": pin["digest"], "state": WITHDRAWN, "pin": pin, "declared": None})
    for row in rows:
        row["disposition"] = disposition(ctx, row["state"])
        if row["disposition"] not in DISPOSITIONS:
            raise ProvenanceRefused(
                f"state {row['state']!r} is given the disposition {row['disposition']!r}; the "
                f"effects this kit can carry out are {list(DISPOSITIONS)}")
    return rows


def _says(ctx, key: str, word: str, what: str) -> str:
    return _row(declaration(ctx)[key], "state", word, what)["says"]


def label(ctx, row) -> str:
    """One taken capability on the surface: integrity and authenticity as two separate words,
    each with where it came from. Never folded into one `trusted`."""
    pin = row["pin"] or {}
    integrity = f"{row['state'].upper()}  {row['digest']}"
    if row["state"] in (PINNED, WITHDRAWN):
        integrity += f"  (pinned by {pin['pinned_by']} at {pin['pinned_at']})"
    line = f"  TAKEN  {row['capability']}@{row['version']}  integrity {integrity}"
    if pin.get("authenticity") and row["state"] in (PINNED, WITHDRAWN):
        found = pin["authenticity"]
        word = _row(declaration(ctx)["authenticity"], "state", found["state"], "authenticity")
        line += (f"\n         authenticity {word['standing'].upper()}: {found['state']}"
                 f" (read at {found['taken_at']}) -- {word['says']}")
    return line + f"\n         {_says(ctx, 'states', row['state'], 'state')}"


def report(ctx, rows) -> None:
    if not rows:
        print("  TAKEN  none -- every capability in force was issued by this kit and is "
              "accounted for by its lock")
    for row in rows:
        print(label(ctx, row))


def _argv(template: list, values: dict) -> list:
    """A declared argv with its WHOLE-token placeholders filled. A token is a placeholder only if
    it is exactly `{name}`: nothing is formatted, split or evaluated, so a value can never become
    a second argument or a flag."""
    out = []
    for token in template:
        if token.startswith("{") and token.endswith("}"):
            name = token[1:-1]
            if name not in values:
                raise ProvenanceRefused(f"a verifier's argv names {token!r}, which is not one of "
                                        f"{sorted(values)}")
            out.append(values[name])
        else:
            out.append(token)
    return out


def authenticate(ctx, capability, measured: str, moment: str) -> dict:
    """Attempt authenticity, DELEGATED; return what was established, in a declared word. Every
    path out of here that is not `verified` is a named absence -- except `refuted`, which is
    evidence AGAINST and is refused by the caller, never recorded as a mere absence."""
    found = {"state": UNSIGNED, "taken_at": moment}
    claim = capability.raw.get(CLAIM)
    if not claim:
        return found
    found.update({"verifier": claim["verifier"], "signer": claim["signer"]})
    document = declaration(ctx)
    verifier = next((v for v in document["verifiers"] if v["id"] == claim["verifier"]), None)
    signature = ctx.manifest.path(claim["signature"])
    if verifier is None:
        return found | {"state": UNKNOWN_VERIFIER}
    if not signature.is_file():
        return found | {"state": SIGNATURE_MISSING}
    if not ctx.workspace.exists(verifier["trust_root"]) or not any(
            line.strip() and not line.strip().startswith(verifier["comment"])
            for line in ctx.workspace.read_bytes(verifier["trust_root"]).decode(
                "utf-8", "replace").splitlines()):
        return found | {"state": NO_TRUST_ROOT}
    program = shutil.which(verifier["argv"][0])
    if program is None:
        return found | {"state": VERIFIER_ABSENT}
    root = ctx.workspace.path(verifier["trust_root"])
    statement = (document["statement"].replace("{capability}", capability.id)
                 .replace("{version}", capability.version).replace("{digest}", measured))
    argv = _argv(verifier["argv"][1:], {"trust_root": str(root), "signer": claim["signer"],
                                         "namespace": verifier["namespace"],
                                         "signature": str(signature)})
    ran = subprocess.run([program, *argv], input=statement.encode("utf-8"), capture_output=True)
    return found | {
        "state": VERIFIED if ran.returncode == 0 else REFUTED,
        "trust_root_digest": hashlib.sha256(root.read_bytes()).hexdigest(),
        "evidence": (ran.stdout + ran.stderr).decode("utf-8", "replace").strip()[:400],
    }


def judge(ctx, capabilities, who, when: str, at_door: bool) -> list:
    """Hold every taken capability to its pin, and return the pins the estate should carry.

    Refusals come first and are total: bytes that are not what was pinned, or a version older than
    the one pinned, stop the run before any write, and no approval opens them -- a door that
    could re-pin a drift would make the pin a formality. A capability met for the first time is a
    DOOR: an approval on this run walks it and its name goes on the pin."""
    recorded = estate_module.read(ctx)
    rows = survey(ctx, capabilities, (recorded or {}).get("taken", []))
    report(ctx, rows)
    refused = [row for row in rows if row["disposition"] == REFUSE]
    if refused:
        raise ProvenanceRefused(
            f"{len(refused)} capability(ies) this kit did not issue cannot be taken:\n  "
            + "\n  ".join(f"{row['state']}  {row['capability']}@{row['version']}  {row['digest']}"
                          f"  -- pinned {row['pin']['version']} {row['pin']['digest']} by "
                          f"{row['pin']['pinned_by']} at {row['pin']['pinned_at']}"
                          for row in refused))
    # A pin written at arrival (trust-on-first-use) waits at the same door as a first contact: its
    # bytes already equal it (a drift was refused above), and the approval ATTESTS it here.
    waiting = [row for row in rows if row["disposition"] == DOOR
               or (row["disposition"] == HOLD and unattested(row["pin"]))]
    if waiting and not who:
        if at_door:
            doors.refuse(
                f"{len(waiting)} capability(ies) this kit did not issue have never been pinned "
                f"by this host: " + ", ".join(f"{r['capability']}@{r['version']} ({r['state']})"
                                              for r in waiting),
                "person who owns this host",
                "init --root <host> --approve <who>",
                "Taking bytes from a publisher on nobody's word is the trust hole a pin closes; "
                "the approval records who took them, when, and what they digested to.")
        return [row["pin"] for row in rows if row["pin"] and row["disposition"] != DOOR]
    pins = []
    for row in rows:
        attesting = row["disposition"] == HOLD and unattested(row["pin"])
        if row["disposition"] != DOOR and not attesting:
            pins.append(row["pin"])
            continue
        found = authenticate(ctx, row["declared"], row["digest"], when)
        if attesting and found["state"] != REFUTED:
            pin = dict(row["pin"], authenticity=found,
                       trust={"basis": ATTESTED, "attested_by": who, "attested_at": when})
            pins.append(pin)
            row.update({"pin": pin})
            print(f"  ATTESTED {row['capability']}@{row['version']}  {row['digest']}  pinned at "
                  f"arrival by {pin['pinned_by']} at {pin['pinned_at']}; attested by {who} at "
                  f"{when}  -- authenticity {found['state']}")
            continue
        if found["state"] == REFUTED:
            raise ProvenanceRefused(
                f"{row['capability']}@{row['version']} claims a signature by {found['signer']!r} "
                f"that {found['verifier']} rejected against this host's trust root -- "
                f"{found['state']}: "
                f"{found['evidence']}")
        pin = {"capability": row["capability"], "version": row["version"],
               "digest": row["digest"], "pinned_by": who, "pinned_at": when,
               "authenticity": found}
        if row["pin"]:
            pin["supersedes"] = {"version": row["pin"]["version"], "digest": row["pin"]["digest"]}
        pins.append(pin)
        row.update({"pin": pin, "state": PINNED})
        print(f"  PINNED {row['capability']}@{row['version']}  {row['digest']}  by {who} at {when}"
              f"  -- authenticity {found['state']}")
    return sorted(pins, key=lambda pin: pin["capability"])
