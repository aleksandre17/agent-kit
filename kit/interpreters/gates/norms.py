"""Gate kind for the NORMATIVE TREE: every norm an agent is held to forms one coherent tree (ADR-024).

Doctrine documents (the `cardinal` contract) are five levels of one grammar, told apart by genre:
cardinals (L0, never waived), doctrines (L1, a concern area), rules (L2, with an RFC 2119 modality),
their enforcement (L3: a gate, an edit gate, a verb -- or an enforcer a taken adapter vouches for in the
host, `<prefix>:<name>` -- a MUST names) and procedures (L4: a skill).
Every norm below a cardinal derives from exactly one parent (`derives_from`), so the tree is a tree.
A host instantiates rules through its stances: `extends` tightens, `narrows` loosens -- and a loosening
holds only with an exception that names its ADR, its owner, its expiry and its compensating control.

This gate checks, deterministically, and names each finding by its code:

  NT-ORPHAN       a norm below a cardinal with no parent, or a parent nobody publishes
  NT-CYCLE        a chain of parents that returns to itself
  NT-CONTRADICTS  two rules on one subject whose modalities oppose
  NT-UNENFORCED   a MUST that names no enforcer this host has
  NT-LOOSENED     a host stance that narrows a rule without an exception
  NT-EXPIRED      an exception past its expiry
"""

from __future__ import annotations

import re

import declared

KIND = "norms-coherent"
NORMS = ({declared.CONTRACT: "cardinal"},)
GENRES = ({declared.CONTRACT: "doctrine"}, "genres")
#: Each modality's polarity and strength (RFC 2119): opposite polarities on one subject contradict.
MODALITIES = {"MUST": (1, 3), "SHOULD": (1, 2), "MAY": (0, 1), "SHOULD NOT": (-1, 2), "MUST NOT": (-1, 3)}
VOCABULARY = ({declared.CONTRACT: "doctrine"}, "stance_vocabulary")
#: The enforcers a taken ADAPTER vouches for: found by their contract, never by a product's name.
VOUCHED = {declared.CONTRACT: "enforcers"}


def norms_of(ctx) -> list:
    """Every norm the host's declared sources carry -- read by `check` and by `prove`."""
    return _norms(ctx)


def _norms(ctx) -> list:
    found = []
    for name in declared.named(ctx.enabled_capabilities(), NORMS[0]):
        for value in declared.sources(ctx, [name]).values():
            found += value if isinstance(value, list) else []
    return found


def _enforcers(ctx) -> set:
    known = {f"gate:{g['id']}" for c in ctx.enabled_capabilities() for g in c.gates}
    known |= {f"edit-gate:{r['id']}" for r in declared.rules(ctx, {declared.CONTRACT: "edit-gate"}, "gates")}
    known |= {f"verb:{p.stem}" for p in (ctx.manifest.root / "interpreters" / "verbs").glob("*.py")}
    return known | _vouched(ctx)


def _vouched(ctx) -> set:
    """`<prefix>:<key>` for every key the HOST declares, not empty, under the pointer of the file each
    `enforcers` document names -- what an adapter can find in this host, and nothing it merely knows.
    A file that is absent or unreadable vouches for nothing."""
    known = set()
    for document in declared.sources(ctx, VOUCHED).values():
        if not ctx.workspace.exists(document["path"]):
            continue
        try:
            value = ctx.workspace.read_json(document["path"])
        except ValueError:
            continue
        for step in document["pointer"].split("."):
            value = value.get(step) if isinstance(value, dict) else None
        if isinstance(value, dict):
            known |= {f"{document['prefix']}:{key}" for key, given in value.items() if given}
    return known


_ADDRESS = re.compile(r"^([^@#]+)@[^#]+#(.+)$")


def readdressed(norms: list, stances: list) -> dict:
    """{old address: new}: every stance whose address no norm in force publishes, where exactly one norm in
    force has the same publisher and name at another version -- a stance a new version of its bundle left
    answering nothing. Ambiguous or unrelated addresses are not guessed at."""
    in_force = {n["id"] for n in norms}
    by_name = {}
    for identity in in_force:
        found = _ADDRESS.match(identity)
        if found:
            by_name.setdefault(found.groups(), []).append(identity)
    moves = {}
    for stance in stances:
        identity = str(stance.get("id") or "")
        found = _ADDRESS.match(identity)
        if identity in in_force or not found:
            continue
        candidates = by_name.get(found.groups(), [])
        if len(candidates) == 1:
            moves[identity] = candidates[0]
    return moves


def judged(norms: list, stances: list, enforcers: set, today: str, deriving: set, loosening: set) -> list:
    """`deriving`: the genres the grammar declares stand below a parent; `loosening`: the stance words
    it declares loosen what they answer."""
    failures = []
    by_id = {n["id"]: n for n in norms}
    for norm in norms:
        parent = norm.get("derives_from")
        if (norm["genre"] in deriving or parent) and (not parent or parent not in by_id):
            failures.append(f"NT-ORPHAN {norm['id']}: derives from {parent!r}, which no document in force publishes")
    for norm in norms:
        seen, current = [], norm["id"]
        while current in by_id and by_id[current].get("derives_from"):
            if current in seen:
                failures.append(f"NT-CYCLE {norm['id']}: {' -> '.join(seen + [current])}")
                break
            seen.append(current)
            current = by_id[current]["derives_from"]
    rules = [n for n in norms if n.get("modality")]
    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            if a.get("subject") and a.get("subject") == b.get("subject") \
                    and MODALITIES[a["modality"]][0] * MODALITIES[b["modality"]][0] < 0:
                failures.append(f"NT-CONTRADICTS {a['id']} ({a['modality']}) and {b['id']} ({b['modality']}) "
                                f"on the subject {a['subject']!r}")
    for rule in rules:
        if MODALITIES[rule["modality"]][1] == 3 and not set(rule.get("enforced_by", [])) & enforcers:
            failures.append(f"NT-UNENFORCED {rule['id']}: a {rule['modality']} names no enforcer this host has "
                            f"({rule.get('enforced_by') or 'none'})")
    for stance in stances:
        exception = stance.get("exception")
        if stance.get("stance") in loosening and stance["id"] in by_id and by_id[stance["id"]].get("modality") \
                and not exception:
            failures.append(f"NT-LOOSENED {stance['id']}: narrowed without an exception (its ADR, owner, expiry "
                            f"and compensating control)")
        if exception and exception["expires"] < today:
            failures.append(f"NT-EXPIRED {stance['id']}: its exception expired on {exception['expires']}")
    for old, new in sorted(readdressed(norms, stances).items()):
        failures.append(f"NT-READDRESS {old}: no norm in force has this address, {new} does -- the stance answers "
                        f"nothing until it is re-addressed (upgrade --mode addresses)")
    return failures


def _held(ctx, params) -> list:
    norms = _norms(ctx)
    local = next((i for c in ctx.enabled_capabilities() for i in c.installs if i.get("validates") == "doctrine"), None)
    stances = []
    if local and ctx.workspace.exists(local["target"]):
        stances = ctx.workspace.read_json(local["target"]).get("stances", [])
    counts = {}
    for norm in norms:
        counts[norm["genre"]] = counts.get(norm["genre"], 0) + 1
    print(f"        READ the normative tree: " + (", ".join(f"{n} {g}(s)" for g, n in sorted(counts.items())) or "no norm")
          + f"; {len(stances)} host stance(s)")
    deriving = {g["id"] for g in declared.rules(ctx, *GENRES) if g.get("derives")}
    loosening = {w["id"] for w in declared.rules(ctx, *VOCABULARY) if w.get("loosens")}
    return judged(norms, stances, _enforcers(ctx), ctx.clock.now()[:10], deriving, loosening)


def _calibrate(host):
    """An unenforced MUST is flagged; the same MUST naming an enforcer the host has is admitted."""
    tree = [{"id": "c@1.0.0#root", "genre": "root"},
            {"id": "c@1.0.0#rule", "genre": "below", "derives_from": "c@1.0.0#root", "modality": "MUST",
             "subject": "s", "enforced_by": ["gate:G"]}]
    return (judged(tree, [], set(), "2026-01-01", {"below"}, set()),
            judged(tree, [], {"gate:G"}, "2026-01-01", {"below"}, set()))


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
