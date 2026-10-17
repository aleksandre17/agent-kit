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
        return weighing.weigh(paths, classes_doc, areas, weighing.loosened(classes_doc, stood, left),
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


def _marks_signed(ctx, params):
    """Where the host declares `owner_signing`, every acceptance a record in the binding places carries
    -- a door's passage, a lowering, a host's install or upgrade, and a review in the name of someone
    who signs -- holds only in a commit that principal SIGNED (ADR-025 amendment 3): a name in a record
    is text anything can write. Marks that stood when signing was set up hold as they were; a mark not
    yet committed is reported, never failed -- it is judged when it is committed."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    declared = (governed.policy or {}).get("owner_signing")
    if not declared:
        return []
    signers = declared["signers"]
    setup = "run, in your own terminal: python <kit>/interpreters/cli.py signer --setup --root ."
    who_signs = signing.principals(ctx.workspace.read_text(signers)) if ctx.workspace.exists(signers) else []
    if not who_signs:
        return [f"owner signing is declared and nobody may sign yet ({signers} names no key) -- {setup}"]
    if ctx.workspace.shallow():
        return ["owner signing: NOT MEASURED -- this clone is shallow, so the commits that carry the marks are "
                "not here to be read; fetch the whole history (fetch-depth: 0)"]
    first, why = ctx.workspace.introduced(signers)
    if first is None:
        return [f"owner signing: NOT MEASURED -- git could not say when {signers} came in: {why}"]
    if not first:
        return [f"{signers} is written and not committed -- commit it signed: git add {signers} && git commit -S"]
    changes, why = ctx.workspace.signed_commits(signers, signers)
    if changes is None:
        return [f"owner signing: NOT MEASURED -- {why}"]
    failures = [f"{signers}: commit {sha[:12]} changed who may sign, and no allowed signer signed it"
                for sha, verdict, _ in changes if sha != first and verdict != "G"]

    def held_in(value) -> dict:
        found = signing.marks(value)
        found.update({key: door for key, door in signing.reviews(value).items() if key[0] in who_signs})
        return found

    def parsed(text):
        try:
            return json.loads(text) if text else None
        except ValueError:
            return None

    places = [p["root"].rstrip("/") for p in ctx.manifest.planes if p["class"] == "binding"]
    places += [i["target"].rstrip("/") for c in capabilities for i in c.installs
               if i.get("class") == "binding" and i.get("mode") == "space"]
    records = sorted({rel for place in places for rel in ctx.workspace.files_under(place) if rel.endswith(".json")})
    for rel in records:
        value = parsed(ctx.workspace.read_text(rel))
        if value is None:
            continue
        before, _ = ctx.workspace.file_at(first, rel)
        held_then = held_in(parsed(before)) if before else {}
        judged = {door: keys for door, keys in signing.doors_of(held_in(value)).items()
                  if not any(key in held_then for key in keys)}
        if not judged:
            continue
        commits, why = ctx.workspace.signed_commits(rel, signers)
        if commits is None:
            failures.append(f"{rel}: NOT MEASURED -- {why}")
            continue
        signed, committed = set(), set()
        for sha, verdict, principal in commits:
            there = held_in(parsed(ctx.workspace.file_at(sha, rel)[0]) or {})
            committed |= set(there)
            if verdict == "G":
                signed |= {key for key in there if key[0] == principal}
        for door, keys in sorted(judged.items()):
            if any(key in signed for key in keys):
                continue
            if not any(key in committed for key in keys):
                print(f"        {rel}: {door} is marked by {keys[0][0]} and not committed yet -- it holds once a "
                      f"commit {keys[0][0]} signs carries it (git commit -S)")
                continue
            failures.append(f"{rel}: {door} is marked by {', '.join(sorted({k[0] for k in keys}))}, and no commit "
                            f"that principal signed carries the mark -- a name is not a signature; it is walked "
                            f"again in a commit they sign (git commit -S)")
    return failures


KINDS = {"marks-signed": _marks_signed, "work-classes-held": _work_classes_held, "deferrals-held": _deferrals_held, "order-held": _order_held,
         "emergencies-repaid": _emergencies_repaid, "ceremony-reported": _ceremony_reported}
#: Every kind here judges by reading the governed records: none of them may prove one (decision 16).
READS_THE_RECORDS = {kind: True for kind in KINDS}
