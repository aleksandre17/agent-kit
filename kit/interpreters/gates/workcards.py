"""Gate kind: the work classes hold -- the host's areas use declared words, and every card that
declares a class keeps what that class owes (ADR-025).

A card that declares NO class and no uncertainty is passed over: it is the ordinary way, and a gate
that held every card in existence to a vocabulary that did not exist when it was written would be
back-filling a declaration nobody made (ADR-020 decision 11). The moment a card names a class -- or
an uncertainty, which raises the class it is read as -- the class is a promise this gate reads:

  * the class and the uncertainty are words the catalogue declares;
  * the class is not lighter than its uncertainty asks;
  * every record the class owes is held by the card from the state its row names on -- reached
    meaning the card stands there now or has passed through it (its history), never a guess at an
    order the lifecycle does not declare.

Records with no `held_by` (the commit) are not read here; a record held by a criterion is held when
the card declares one that needs its class -- the verified passage then proves it.
"""

from __future__ import annotations

import json
from datetime import datetime

import collection
import criteria
import lifecycle as lifecycle_module
import lineage
import signing
import weighing
import workclass


def _reached(card: dict, state: str) -> bool:
    return card.get("state") == state or any(p.get("to") == state
                                             for p in card.get(lifecycle_module.HISTORY, []))


def _work_classes_held(ctx, params):
    found = workclass.declarations(ctx)
    if found is None:
        return []
    classes_doc, areas_doc = found
    try:
        weighing.checked(classes_doc, areas_doc)
    except weighing.WeighError as refused:
        return [f"areas: {refused}"]
    installed = set(criteria.registry())
    failures = [f"evidence: the class {row['id']!r} names the kind of proof {kind!r}, which no resolver "
                f"installed here provides ({', '.join(sorted(installed))})"
                for row in classes_doc["evidence"] for kind in row["yielded_by"] if kind not in installed]
    try:
        criteria.evidence(classes_doc["evidence"])
    except criteria.CriterionError as refused:
        failures.append(f"evidence: {refused}")
    known = {row["id"] for row in classes_doc["evidence"]}
    classes = {row["id"]: row for row in classes_doc["classes"]}
    uncertainty = {row["id"]: row for row in classes_doc["uncertainty"]}
    records = {row["id"]: row for row in classes_doc["records"]}
    members = lineage.among(ctx) or []
    doors, _closed = workclass.lifecycle_flags(ctx)
    decided = workclass.decided(ctx)
    for card in sorted(members, key=lambda c: c["id"]):
        for item in card.get("criteria") or []:
            if criteria.NEEDS in item and item[criteria.NEEDS] not in known:
                failures.append(f"{card['id']}: the criterion {item.get('id')!r} needs {item[criteria.NEEDS]!r} "
                                f"evidence, which the scale does not declare ({', '.join(sorted(known))})")
        if "class" not in card:
            # A card that says what kind of work it is (its uncertainty) and no class is read at the
            # class that uncertainty asks -- a classless `chaotic` card is a `major` one, not a pass.
            plain = weighing.lightest_with(classes_doc, "card")
            raised, _why = weighing.card_floor(classes_doc, card, plain)
            if raised == plain:
                continue
            card = dict(card, **{"class": raised})
        name, shaped = card["id"], card["class"]
        if shaped not in classes:
            failures.append(f"{name}: declares the class {shaped!r}, which the catalogue does not "
                            f"({', '.join(classes)})")
            continue
        if classes[shaped].get("expedite"):
            failures.append(f"{name}: is shaped {shaped}, an expedite class -- an emergency is declared in a "
                            f"commit's trailer, and the card that repays it is shaped as the work it was")
            continue
        if (classes[shaped].get("doors") and card.get("state") in classes_doc["working_states"]
                and not weighing.bet(card, doors)):
            failures.append(f"{name}: is {card.get('state')} as {shaped}, whose class has doors, and never "
                            f"passed one -- the owner bets it before work is done under it")
        domain = card.get("uncertainty")
        if domain is not None:
            if domain not in uncertainty:
                failures.append(f"{name}: declares the uncertainty {domain!r}, which the catalogue does "
                                f"not ({', '.join(uncertainty)})")
            elif not weighing.heavier_or_equal(classes_doc, shaped, uncertainty[domain]["at_least"]):
                failures.append(f"{name}: shaped {shaped}, but {domain} work walks at least "
                                f"{uncertainty[domain]['at_least']} -- re-shape it (a heavier class is the owner's bet)")
        for record in classes[shaped]["requires"]:
            holder = records[record].get("held_by")
            if holder and _reached(card, holder["from"]) and not weighing.holds(card, holder, members, decided):
                where = ("a card hanging under it" if holder.get("children")
                         else f"a criterion that needs {holder['criterion_needs']}" if "criterion_needs" in holder
                         else f"`{holder['field']}`")
                failures.append(f"{name}: a {shaped} card owes its {record} from {holder['from']} on, "
                                f"held by {where}, and it has none")
    return failures


def _deferrals_held(ctx, params):
    """A deferred card whose trigger HOLDS is due, and is reported until it leaves the deferring state;
    a deferred card with no trigger is counted and named, never failed -- it is an honest state that
    has not yet said what would end it (ADR-025 decision 8)."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    deferring = {s["id"] for s in governed.states if s.get("defers")}
    failures, untriggered = [], []
    for card in sorted(governed.members.value, key=lambda c: c["id"]):
        if card.get(governed.state_field) not in deferring:
            continue
        trigger = card.get("due_when")
        if trigger is None:
            untriggered.append(card["id"])
            continue
        verdict = criteria.resolve(ctx, trigger, card)
        if verdict.holds is True:
            failures.append(f"{card['id']}: DUE -- the trigger it was deferred on holds ({verdict.reading}). "
                            f"Shape it again or park it with a new trigger, on the record")
    if untriggered:
        print(f"        deferred with no trigger: {len(untriggered)} -- {', '.join(untriggered)}")
    return failures


def _after_of(members: dict) -> dict:
    return {identity: list(card.get("after") or []) for identity, card in members.items()}


def _cycle(edges: dict):
    """One cycle through the `after` edges, as a path, or None."""
    state: dict = {}

    def visit(node, trail):
        state[node] = "open"
        for nxt in edges.get(node, []):
            if state.get(nxt) == "open":
                return trail + [node, nxt]
            if nxt in edges and state.get(nxt) is None:
                found = visit(nxt, trail + [node])
                if found:
                    return found
        state[node] = "done"
        return None

    for node in sorted(edges):
        if state.get(node) is None:
            found = visit(node, [])
            if found:
                return found
    return None


def _order_held(ctx, params):
    """The order between cards is an order: every name resolves, no card comes after itself through
    any chain, and finished work that STOPS holding is reported REGRESSED with everything that came
    after it -- invalidation read from the criteria, never kept in a ledger (ADR-025 decision 9)."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    members = {c["id"]: c for c in governed.members.value}
    edges = _after_of(members)
    failures = [f"{card}: comes after {name!r}, which this host does not hold"
                for card, names in sorted(edges.items()) for name in names if name not in members]
    loop = _cycle(edges)
    if loop:
        failures.append(f"the order is a cycle: {' -> '.join(loop)} -- no part of it can ever start")
    closed = {s["id"] for s in governed.states if s.get("closed")}
    for identity, card in sorted(members.items()):
        if card.get(governed.state_field) not in closed:
            continue
        refuted = [item.get("id") for item, verdict in criteria.read(ctx, card, governed.spec["criteria"]) if verdict.holds is False]
        if refuted:
            later = sorted(i for i, names in edges.items() if identity in names)
            failures.append(f"{identity}: REGRESSED -- finished, and {', '.join(map(str, refuted))} no longer "
                            f"holds" + (f"; it came before {', '.join(later)}" if later else ""))
    return failures


def _days_between(earlier: str, later: str):
    try:  # a trailing Z is UTC; Python 3.10's fromisoformat does not read it
        return (datetime.fromisoformat(str(later).replace("Z", "+00:00"))
                - datetime.fromisoformat(str(earlier).replace("Z", "+00:00"))).total_seconds() / 86400
    except (TypeError, ValueError):
        return None


def _owed_by(ctx, classes_doc: dict, sha: str) -> dict:
    """What an emergency commit owes afterwards: the verdict of its own change, weighed by the areas its
    parent held -- the class it would have walked had there been time."""
    rel = workclass.areas_target(ctx)
    stood = workclass._parsed_any(ctx.workspace.file_at(f"{sha}^", rel)[0]) if rel else None
    left = workclass._parsed_any(ctx.workspace.file_at(sha, rel)[0]) if rel else None
    areas = stood or left or {"default_undo": classes_doc["undo"][0]["id"], "max_areas": {}, "areas": []}
    paths = ctx.workspace.commit_paths(sha)[0] or []
    try:
        commands = (workclass.commands_at(ctx, lambda rel: ctx.workspace.file_at(f"{sha}^", rel)[0]),
                    workclass.commands_at(ctx, lambda rel: ctx.workspace.file_at(sha, rel)[0]))
        return weighing.weigh(paths, classes_doc, areas, weighing.loosened(classes_doc, stood, left, commands),
                              weighing.loosened_areas(classes_doc, stood, left))[1]
    except weighing.WeighError:  # a scale nobody can read weighs as the heaviest class, never the lightest
        row = [r for r in classes_doc["classes"] if not r.get("expedite")][-1]
        return {"class": row, "requires": list(row["requires"]), "why": "its areas could not be read"}


def _pays(classes_doc: dict, card: dict, owed: dict, cards: list, doors, decided) -> list:
    """Why a card naming a debt does not pay it -- empty when it does: it is shaped at least as the
    commit weighed, holds every record that weight owes, and passed the owner's door where its class
    has one. A stub naming the commit is a promise, not the payment."""
    rank = {row["id"]: row for row in classes_doc["classes"]}
    shaped, _why = weighing.card_floor(classes_doc, card, weighing.lightest_with(classes_doc, "card"))
    if shaped not in rank or rank[shaped].get("expedite"):
        return [f"it is shaped {shaped!r}, which pays no debt"]
    said = []
    if not weighing.heavier_or_equal(classes_doc, shaped, owed["class"]["id"]):
        said.append(f"it is shaped {shaped}, and the change weighs {owed['class']['id']} ({owed['why']})")
    records = {row["id"]: row for row in classes_doc["records"]}
    for record in owed["requires"]:
        holder = records.get(record, {}).get("held_by")
        if holder and not weighing.holds(card, holder, cards, decided):
            said.append(f"it does not hold the {record} that weight owes")
    if rank[shaped].get("doors") and doors and not weighing.bet(card, doors):
        said.append(f"its class {shaped} has doors, and the owner never passed it through one")
    return said


def _emergencies_repaid(ctx, params):
    """Every emergency commit is a debt with a clock: a card naming it in `repays` pays it once the card
    is the work the commit skipped -- shaped at least as the commit weighs by its parent's areas,
    holding what that weight owes, bet where its class has doors. Past the host's declared days an
    unpaid one fails; before them it is reported with what is left. A host that declares no days is
    told what it owes and is never failed (ADR-025 decision 6)."""
    found = workclass.declarations(ctx)
    if found is None:
        return []
    classes_doc, _areas = found
    expedite = [row["id"] for row in classes_doc["classes"] if row.get("expedite")]
    if not expedite:
        return []
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    # A debt stays paid once its card is archived: the archive is read for `repays` too.
    archived = []
    for item in governed.capability.installs:
        if item.get("mode") == "space" and not item.get("reads_as") and item.get("validates") == "card":
            for rel in ctx.workspace.files_under(item["target"].rstrip("/")):
                if rel.endswith(".json"):
                    try:
                        archived.append(ctx.workspace.read_json(rel))
                    except ValueError:
                        continue
    every = [card for card in [*governed.members.value, *archived] if isinstance(card, dict)]
    doors, _closed = workclass.lifecycle_flags(ctx)
    decided = workclass.decided(ctx)
    limit = (governed.policy or {}).get("emergency_debt_days")
    now = ctx.clock.now()
    failures = []
    for identity in expedite:
        commits, why = ctx.workspace.commits_trailed(classes_doc["trailers"]["class"], identity)
        if commits is None:
            print(f"        emergencies: NOT MEASURED -- git could not list them: {why}")
            return []
        for sha, at in commits:
            naming = [card for card in every if any(sha.startswith(str(p)) for p in card.get("repays") or [] if p)]
            short = []
            if naming:
                owed = _owed_by(ctx, classes_doc, sha)
                verdicts = {card.get("id"): _pays(classes_doc, card, owed, every, doors, decided) for card in naming}
                if any(not why for why in verdicts.values()):
                    continue
                short = [f"{identity_of}: {'; '.join(why)}" for identity_of, why in sorted(verdicts.items())]
            unpaid = (f"the card(s) naming it do not pay it yet -- {' | '.join(short)}" if short
                      else "no card repays it")
            age = _days_between(at, now)
            if limit is not None and age is not None and age > limit:
                failures.append(f"{sha[:12]}: an {identity} change {age:.0f} day(s) old, past the {limit} this "
                                f"host declares, and {unpaid} -- name it in the `repays` of a card shaped as the work")
            else:
                left = "" if limit is None or age is None else f", {max(0, limit - age):.0f} day(s) left"
                print(f"        owed: {sha[:12]} ({identity}, {at}{left}) -- {unpaid}")
    return failures


def _ceremony_reported(ctx, params):
    """What each class of finished work cost, read from the cards alone: how many, how many records
    they carry, and their lead time from created to finished -- DORA's lead time, per class. A
    reading, never a verdict: whether a class costs too much is the owner's to judge (ADR-025
    decision 11)."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    closed = {s["id"] for s in governed.states if s.get("closed")}
    by_class: dict = {}
    for card in governed.members.value:
        if card.get(governed.state_field) not in closed:
            continue
        entered = next((p.get("at") for p in reversed(card.get(lifecycle_module.HISTORY, []))
                        if p.get("to") in closed), None)
        days = _days_between(card.get(lifecycle_module.CREATED_AT), entered) if entered else None
        row = by_class.setdefault(card.get("class", "unclassed"), {"finished": 0, "declared": 0, "days": []})
        row["finished"] += 1
        row["declared"] += len(card.get(governed.spec["criteria"]) or [])
        if days is not None:
            row["days"].append(days)
    for identity, row in sorted(by_class.items()):
        lead = sorted(row["days"])
        median = f"{lead[len(lead) // 2]:.1f} day(s)" if lead else "unknown"
        print(f"        ceremony: {identity}: {row['finished']} finished, {row['declared']} criteria, "
              f"median lead time {median}")
    return []


def _parsed(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


class _History:
    """What the gate over owner marks reads of the history, read once: the order of commits, each
    commit's parent, and every trust root's ACCEPTED versions -- a change to who may sign is accepted
    only when a signer the root allowed at the commit's parent signed it; the first version that names a
    principal is the bootstrap, trusted on first use (ADR-025 amendment 3)."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.order = workspace.commit_order()
        self._parents: dict = {}
        self._roots: dict = {}

    def at(self, sha: str) -> int:
        return self.order.get(sha, -1)

    def parent(self, sha: str) -> str:
        if sha not in self._parents:
            self._parents[sha] = self.workspace.parent(sha)
        return self._parents[sha]

    def text(self, sha: str, rel: str) -> str:
        return (self.workspace.file_at(sha, rel)[0] or "") if sha and rel else ""

    def root(self, rel: str) -> dict:
        """{accepted: [(position, sha, text)], bootstrap: sha, rejected: [sha], why}, oldest first."""
        if rel in self._roots:
            return self._roots[rel]
        made = self._roots[rel] = {"accepted": [], "bootstrap": "", "rejected": [], "why": None}
        commits, made["why"] = self.workspace.history(rel)
        for sha, _path in commits or []:
            text = self.text(sha, rel)
            if not made["accepted"]:
                if signing.principals(text):
                    made["accepted"].append((self.at(sha), sha, text))
                    made["bootstrap"] = sha
                continue
            if text == signing.root_at(made["accepted"], self.at(self.parent(sha))):
                continue
            verdict, _principal = self.verdict(sha, rel)
            (made["accepted"].append((self.at(sha), sha, text)) if verdict == "G" else made["rejected"].append(sha))
        return made

    def verdict(self, sha: str, root_rel: str) -> tuple:
        """(git's verdict, the principal) on one commit, against `root_rel` as ACCEPTED at its parent --
        never the root the tree holds now, never one the commit itself wrote (but the bootstrap's own)."""
        chain = self.root(root_rel)
        if sha == chain["bootstrap"]:
            held = chain["accepted"][0][2]
        else:
            held = signing.root_at(chain["accepted"], self.at(self.parent(sha))) if self.parent(sha) else ""
        return self.workspace.signature(sha, held) if held else ("", "")


def _declaration_held(seen: _History, policy_rel: str, default_root: str) -> dict:
    """The policy's `owner_signing` as its history holds it: {accepted, protected, since, refused}. Once a
    declaration stands in a signed commit it is PROTECTED -- removing it or repointing its signers holds
    only in a commit a signer the declared root allowed at the parent signed; a change nobody allowed
    signed is refused, and the declaration it tried to undo goes on binding. `since` is the first commit
    that declared it."""
    held = {"accepted": None, "protected": False, "since": "", "refused": []}
    commits, _why = seen.workspace.history(policy_rel)
    for sha, path in commits or []:
        value = _parsed(seen.text(sha, path))
        value = value.get("owner_signing") if isinstance(value, dict) else None
        if value == held["accepted"] and (held["protected"] or value is None):
            continue
        judged_by = (held["accepted"] if held["protected"] else value) or {}
        root_rel = judged_by.get("signers") or default_root
        signed = bool(root_rel) and seen.verdict(sha, root_rel)[0] == "G"
        if held["protected"]:
            if not signed:
                held["refused"].append((sha, value))
                continue
            held["accepted"], held["protected"] = value, value is not None
            continue
        held["accepted"], held["protected"] = value, value is not None and signed
        if value is not None and not held["since"]:
            held["since"] = sha
    return held


def _marks_signed(ctx, params):
    """Where the host declares `owner_signing`, every acceptance a record in the binding places carries
    -- a door's passage, a lowering, a host's install or upgrade, and a review in the name of someone
    who signs -- holds only when a commit that principal SIGNED introduced it (ADR-025 amendment 3): a
    name in a record is text anything can write. Each signature is read against the trust root as it was
    accepted at the commit's parent; a mark is where it stands, who made it and when, and a commit is
    credited only with the marks it brought; a card the archive moved keeps its history. Marks that stood
    when signing was set up -- the later of the first trust root that names a principal and the first
    policy that declares it -- hold as they were; a mark not yet committed is reported, never failed."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    in_tree = (governed.policy or {}).get("owner_signing")
    policy_rel = next((i["target"] for i in governed.capability.installs if i.get("reads_as") == "policy"), "")
    rooted = signing.trust_root(capabilities)
    default_root = rooted[0] if rooted else ""
    setup = "run, in your own terminal: python <kit>/interpreters/cli.py signer --setup --root ."
    if ctx.workspace.shallow():
        return [] if in_tree is None else [
            "owner signing: NOT MEASURED -- this clone is shallow, so the commits that carry the marks are "
            "not here to be read; fetch the whole history (fetch-depth: 0)"]
    seen = _History(ctx.workspace)
    held = _declaration_held(seen, policy_rel, default_root)
    failures = []
    committed_value = _parsed(seen.text("HEAD", policy_rel))
    committed_value = committed_value.get("owner_signing") if isinstance(committed_value, dict) else None
    if held["protected"] and committed_value != held["accepted"]:
        failures += [f"{policy_rel}: commit {sha[:12]} {'removed owner_signing' if value is None else 'changed owner_signing'}"
                     f", and no allowed signer signed it -- the declaration it tried to undo still binds"
                     for sha, value in held["refused"]]
    if held["protected"] and in_tree != held["accepted"]:
        print(f"        {policy_rel}: owner_signing is changed and not committed -- it holds once an allowed "
              f"signer signs the commit (git commit -S); until then the signed declaration binds")
    declared = held["accepted"] if held["protected"] else in_tree
    if declared is None:  # `{}` is a declaration: signing, against the host's one trust root
        return failures
    signers = declared.get("signers") or default_root
    if not signers:
        return failures + ["owner signing is declared and no trust root is: no capability declares a verifier"]
    chain = seen.root(signers)
    if chain["why"]:
        return failures + [f"owner signing: NOT MEASURED -- git could not read the history of {signers}: {chain['why']}"]
    if not chain["accepted"]:
        if signing.principals(ctx.workspace.read_text(signers) if ctx.workspace.exists(signers) else ""):
            print(f"        {signers} names a signer and is not committed -- commit it signed: "
                  f"git add {signers} {policy_rel} && git commit -S")
            return failures
        return failures + [f"owner signing is declared and nobody may sign yet ({signers} names no key) -- {setup}"]
    accepted = chain["accepted"][-1]
    if seen.text("HEAD", signers) != accepted[2]:
        failures += [f"{signers}: commit {sha[:12]} changed who may sign, and no allowed signer signed it"
                     for sha in chain["rejected"] if seen.at(sha) > accepted[0]]
    if not held["since"]:
        print(f"        {policy_rel}: owner_signing is declared and not committed -- marks are judged from the "
              f"commit that declares it")
        return failures
    baseline = max((chain["bootstrap"], held["since"]), key=seen.at)
    who_signs = signing.principals(accepted[2])

    def held_in(value) -> dict:
        found = signing.marks(value)
        found.update({key: door for key, door in signing.reviews(value).items() if signing.who(key) in who_signs})
        return found

    def holds(keys, door, items) -> bool:
        return any((key, door) in items for key in keys)

    places = [p["root"].rstrip("/") for p in ctx.manifest.planes if p["class"] == "binding"]
    places += [i["target"].rstrip("/") for c in capabilities for i in c.installs
               if i.get("class") == "binding" and i.get("mode") == "space"]
    records = sorted({rel for place in places for rel in ctx.workspace.files_under(place) if rel.endswith(".json")})
    for rel in records:
        value = _parsed(ctx.workspace.read_text(rel))
        now = held_in(value) if value is not None else {}
        if not now:
            continue
        commits, then_path = None, rel
        then_text, _ = ctx.workspace.file_at(baseline, rel)
        if then_text is None:  # moved since (the archive): the path it had where signing began
            commits, why = ctx.workspace.history(rel, follow=True)
            if commits is None:
                failures.append(f"{rel}: NOT MEASURED -- {why}")
                continue
            then_path = next((path for sha, path in reversed(commits) if seen.at(sha) <= seen.at(baseline)), "")
            then_text = seen.text(baseline, then_path)
        then = set(held_in(_parsed(then_text) or {}).items())
        judged = {door: keys for door, keys in signing.doors_of(now).items() if not holds(keys, door, then)}
        if not judged:
            continue
        if commits is None:
            commits, why = ctx.workspace.history(rel, follow=True)
            if commits is None:
                failures.append(f"{rel}: NOT MEASURED -- {why}")
                continue
        signed, before_path = set(), then_path
        for sha, path in commits:
            if seen.at(sha) <= seen.at(baseline):
                before_path = path
                continue
            after = held_in(_parsed(seen.text(sha, path)) or {})
            before = held_in(_parsed(seen.text(seen.parent(sha), before_path or path)) or {})
            before_path = path
            brought = signing.introduced(after, before)
            if not brought:
                continue
            verdict, principal = seen.verdict(sha, signers)
            if verdict == "G":
                signed |= {(key, door) for key, door in brought.items() if signing.who(key) == principal}
        committed = set(held_in(_parsed(seen.text("HEAD", commits[-1][1])) or {}).items()) if commits else set()
        for door, keys in sorted(judged.items()):
            if holds(keys, door, signed):
                continue
            names = ", ".join(sorted({signing.who(k) for k in keys}))
            if not holds(keys, door, committed):
                print(f"        {rel}: {door} is marked by {names} and not committed yet -- it holds once a "
                      f"commit {names} signs carries it (git commit -S)")
                continue
            failures.append(f"{rel}: {door} is marked by {names}, and no commit that principal signed "
                            f"introduced the mark -- a name is not a signature; it is walked again in a commit "
                            f"they sign (git commit -S)")
    return failures


KINDS = {"marks-signed": _marks_signed, "work-classes-held": _work_classes_held, "deferrals-held": _deferrals_held, "order-held": _order_held,
         "emergencies-repaid": _emergencies_repaid, "ceremony-reported": _ceremony_reported}
#: Every kind here judges by reading the governed records: none of them may prove one (decision 16).
READS_THE_RECORDS = {kind: True for kind in KINDS}
