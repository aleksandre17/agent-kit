"""A change's class is computed from the areas it touches, and a declared class is a floor (ADR-025)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2] / "kit"
sys.path.insert(0, str(KIT / "interpreters"))

import weighing  # noqa: E402

CLASSES = json.loads((KIT / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))


def areas(*rows, default="reversible", max_areas=None):
    built = []
    for row in rows:
        identity, paths, undo, *extra = row
        built.append({"id": identity, "paths": paths, "undo": undo, "because": "a fixture", **(extra[0] if extra else {})})
    return {"schema_version": 1, "default_undo": default, "max_areas": max_areas or {}, "areas": built}


HOST = areas(("migrations", r"^db/migrations/", "irreversible"),
             ("contracts", r"^api/contracts/", "costly"),
             ("docs", r"^docs/", "reversible"),
             max_areas={"standard": 1})


def weigh(paths, host=HOST):
    sig, verdict = weighing.weigh(paths, CLASSES, host)
    return verdict["class"]["id"], sig, verdict


# -- the computed class ------------------------------------------------------------------------
def test_a_reversible_change_in_one_area_is_standard_and_owes_only_its_commit():
    cls, _, verdict = weigh(["docs/guide.md"])
    assert cls == "standard" and verdict["requires"] == ["commit"]


def test_one_migration_file_makes_the_whole_change_major():
    cls, sig, _ = weigh(["docs/guide.md", "db/migrations/0042_add.sql"])
    assert cls == "major" and sig["undo"] == "irreversible"


def test_a_costly_area_is_normal():
    assert weigh(["api/contracts/orders.json"])[0] == "normal"


def test_breadth_beyond_the_host_limit_raises_a_reversible_change():
    host = areas(("a", r"^a/", "reversible"), ("b", r"^b/", "reversible"), max_areas={"standard": 1})
    assert weigh(["a/x", "b/y"], host)[0] == "normal"


def test_past_every_envelope_the_heaviest_class_stands():
    host = areas(("a", r"^a/", "irreversible"), ("b", r"^b/", "irreversible"), max_areas={"major": 1})
    assert weigh(["a/x", "b/y"], host)[0] == "program"


def test_an_unclaimed_path_carries_the_hosts_default():
    assert weigh(["src/x.py"], areas(default="costly"))[0] == "normal"


def test_nothing_changed_is_standard():
    assert weigh([])[0] == "standard"


# -- tailoring by area -------------------------------------------------------------------------
def test_an_area_raises_the_class_and_owes_its_own_records():
    host = areas(("auth", r"^src/auth/", "reversible", {"at_least": "normal", "requires": ["review"]}))
    cls, _, verdict = weigh(["src/auth/login.py"], host)
    assert cls == "normal" and verdict["requires"] == ["commit", "card", "criteria", "review"]


def test_an_area_never_lowers_the_class():
    host = areas(("m", r"^m/", "irreversible", {"at_least": "standard"}))
    assert weigh(["m/x"], host)[0] == "major"


# -- the floor ---------------------------------------------------------------------------------
def test_a_declared_class_may_be_heavier_never_lighter():
    assert weighing.heavier_or_equal(CLASSES, "major", "normal")
    assert not weighing.heavier_or_equal(CLASSES, "standard", "major")


def test_an_expedite_class_stands_for_any_weight_and_is_never_computed():
    assert weighing.heavier_or_equal(CLASSES, "emergency", "program")
    assert all(weigh(p)[0] != "emergency" for p in (["docs/a"], ["db/migrations/x"]))


@pytest.mark.parametrize("host", [
    areas(("a", r"^a/", "fatal")),
    areas(default="fatal"),
    areas(max_areas={"tiny": 1}),
    areas(("a", r"^a/", "reversible"), ("a", r"^b/", "reversible")),
    areas(("a", r"^a/", "reversible", {"at_least": "tiny"})),
    areas(("a", r"^a/", "reversible", {"requires": ["blessing"]})),
])
def test_a_word_nobody_declared_is_refused(host):
    with pytest.raises(weighing.WeighError):
        weighing.signals(["a/x"], CLASSES, host)


def test_an_undeclared_class_is_refused():
    with pytest.raises(weighing.WeighError):
        weighing.heavier_or_equal(CLASSES, "tiny", "standard")


# -- a commit and its card ---------------------------------------------------------------------
def test_trailers_are_read_from_the_last_paragraph_only():
    message = "feat: x\n\nCard: not-a-trailer-here\nbody text\n\nCard: orders\nWork-Class: normal\n# a comment\n"
    assert weighing.trailers(message) == {"card": "orders", "work-class": "normal"}
    assert weighing.trailers("feat: one line only\n") == {}


def refusals(paths, message, cards=None, host=HOST, doors=None):
    return weighing.commit_refusals(CLASSES, weigh(paths, host)[2], message, cards or {},
                                    DOORS if doors is None else doors)


PROOF = {"id": "c", "statement": "it holds", "proof": {"kind": "artifact-present", "ref": "x"}}
CARD = {"id": "orders", "state": "in-flight", "criteria": [PROOF]}
#: A major card that holds everything its class owes and passed the owner's bet.
MAJOR = {**CARD, "class": "major", "origin": {"kind": "artifact-present", "ref": "docs/decisions/ADR-9.md"},
         "appetite": {"amount": 3, "unit": "days"},
         "criteria": [PROOF, {"id": "r", "statement": "reviewed", "needs": "review",
                             "proof": {"kind": "review-approved", "ref": "r.json"}}],
         "history": [{"from": "shaped", "to": "bet", "at": "t", "by": "owner", "signed_by": "owner"}]}
DOORS = {"bet"}


def test_a_standard_commit_owes_nothing_beyond_itself():
    assert refusals(["docs/a.md"], "docs: a\n") == []


def test_a_normal_commit_must_name_a_card_that_is_being_built():
    assert "owes a card" in refusals(["api/contracts/o.json"], "feat: o\n")[0]
    assert "names no card" in refusals(["api/contracts/o.json"], "feat: o\n\nCard: ghost\n")[0]
    shaped = {**CARD, "state": "shaped"}
    assert "is 'shaped'" in refusals(["api/contracts/o.json"], "feat: o\n\nCard: orders\n", {"orders": shaped})[0]
    assert refusals(["api/contracts/o.json"], "feat: o\n\nCard: orders\n", {"orders": CARD}) == []


def test_a_card_shaped_lighter_than_the_change_is_refused():
    light = {**CARD, "class": "normal"}
    said = refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": light})
    assert any("re-shape the card" in s for s in said)
    assert refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": MAJOR}) == []


def test_a_card_with_no_class_is_read_as_the_lightest_class_that_owes_a_card():
    said = refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": CARD})
    assert "no class on the card, read as normal" in said[0]


def test_a_lighter_declared_class_is_refused_and_an_expedite_one_admitted():
    assert "never lighter" in refusals(["api/contracts/o.json"], "x\n\nWork-Class: standard\nCard: orders\n",
                                       {"orders": CARD})[0]
    assert refusals(["db/migrations/1.sql"], "fix: restore\n\nWork-Class: emergency\n") == []


# -- loosening the scale, lowering a card --------------------------------------------------------
def test_tightening_the_areas_is_free_and_loosening_them_is_named():
    strict = areas(("m", r"^m/", "irreversible", {"requires": ["review"]}), max_areas={"standard": 1})
    assert weighing.loosened(CLASSES, None, strict) == []
    assert weighing.loosened(CLASSES, areas(), strict) == []
    said = weighing.loosened(CLASSES, strict, areas(("m", r"^m/", "costly"), max_areas={"standard": 3}))
    assert any("undo irreversible -> costly" in s for s in said)
    assert any("no longer requires review" in s for s in said)
    assert any("max_areas of standard 1 -> 3" in s for s in said)
    assert weighing.loosened(CLASSES, strict, areas()) and weighing.loosened(CLASSES, strict, None)


def test_a_change_that_loosens_the_areas_owes_a_card():
    _sig, verdict = weighing.weigh(["docs/a.md"], CLASSES, HOST, ["area m removed"])
    assert verdict["class"]["id"] == "normal" and "loosens the areas" in verdict["why"]


def test_lowering_a_card_needs_the_owners_door_on_record():
    before = {"o": {"id": "o", "class": "major"}}
    assert weighing.demotions(CLASSES, before, {"o": {"id": "o", "class": "program"}}) == []
    assert "owner's door" in weighing.demotions(CLASSES, before, {"o": {"id": "o", "class": "normal"}})[0]
    approved = {"id": "o", "class": "normal",
                "reshaped": [{"from": "major", "to": "normal", "at": "t", "by": "dev", "approved_by": "owner"}]}
    assert weighing.demotions(CLASSES, before, {"o": approved}) == []


def test_a_card_line_outside_the_trailer_block_is_named_not_silently_missed():
    said = refusals(["api/contracts/o.json"], "feat: o\n\nCard: orders\n\nCo-Authored-By: x <x@y>\n",
                    {"orders": CARD})
    assert "not in its LAST paragraph" in said[0]
    assert refusals(["api/contracts/o.json"], "feat: o\n\nCard: orders\nCo-Authored-By: x <x@y>\n",
                    {"orders": CARD}) == []



# -- the side doors an audit found, each closed ---------------------------------------------------
def test_a_trailer_spelled_another_way_is_refused_never_read_by_some_readers_only():
    said = refusals(["db/migrations/1.sql"], "fix: x\n\nWork-Class : emergency\n")
    assert said and "is not written `Work-Class: <value>`" in said[0]
    said = refusals(["db/migrations/1.sql"], "fix: x\n\nwork-class: emergency\n")
    assert said and "is not written" in said[0]


def test_an_undeclared_class_in_a_trailer_is_a_refusal_not_a_crash():
    assert "not a declared class" in refusals(["docs/a.md"], "x\n\nWork-Class: Mega\n")[0]
    assert refusals(["db/migrations/1.sql"], "x\n\nWork-Class: Emergency\n") == [], "a value is read in any case"


def test_a_card_is_never_shaped_as_an_expedite_class():
    said = refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": {**MAJOR, "class": "emergency"}})
    assert any("an expedite class" in s for s in said)


def test_reshaping_to_or_from_an_expedite_class_is_the_owners_door():
    before = {"o.json": {"id": "o", "class": "major", "state": "in-flight"}}
    after = {"o.json": {"id": "o", "class": "emergency", "state": "in-flight"}}
    assert "expedite class is declared in a commit" in weighing.demotions(CLASSES, before, after)[0]


def test_a_class_with_doors_needs_the_bet():
    never_bet = {k: v for k, v in MAJOR.items() if k != "history"}
    said = refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": never_bet})
    assert any("never passed one" in s for s in said)


def test_what_a_touched_area_requires_is_held_on_the_card():
    host = areas(("auth", r"^src/auth/", "reversible", {"at_least": "normal", "requires": ["review"]}))
    said = refusals(["src/auth/login.py"], "feat: a\n\nCard: orders\n", {"orders": CARD}, host)
    assert any("owes review" in s for s in said)
    reviewed = {**CARD, "criteria": [PROOF, {"id": "r", "statement": "reviewed", "needs": "review",
                                              "proof": {"kind": "review-approved", "ref": "r.json"}}]}
    assert refusals(["src/auth/login.py"], "feat: a\n\nCard: orders\n", {"orders": reviewed}, host) == []


def test_a_heavier_declaration_owes_the_heavier_records():
    said = refusals(["docs/a.md"], "x\n\nWork-Class: normal\n")
    assert any("owes a card" in s for s in said)


def test_removing_an_unfinished_classed_card_is_a_demotion_and_dropping_a_plain_class_is_not():
    before = {"o.json": {"id": "o", "class": "major", "state": "in-flight"}}
    assert "removed before it finished" in weighing.demotions(CLASSES, before, {})[0]
    assert weighing.demotions(CLASSES, before, {}, closed={"in-flight"}) == []
    plain = {"o.json": {"id": "o", "class": "normal", "state": "in-flight"}}
    assert weighing.demotions(CLASSES, plain, {"o.json": {"id": "o", "state": "in-flight"}}) == []


def test_a_new_area_cheaper_than_the_old_default_loosens():
    said = weighing.loosened(CLASSES, areas(default="costly"), areas(("all", ".*", "reversible"), default="costly"))
    assert said and "cheaper than the costly" in said[0]


# -- the side doors a second audit found, each closed (ADR-025 amendment 2) -----------------------
def test_loosening_an_irreversible_area_walks_the_class_that_area_asked():
    # Found by an audit: emptying the areas cost one normal card, after which a migration landed standard.
    before = areas(("migrations", r"^db/migrations/", "irreversible"), ("docs", r"^docs/", "reversible"))
    after = areas(("docs", r"^docs/", "reversible"))
    lost = weighing.loosened_areas(CLASSES, before, after)
    assert [a["id"] for a in lost] == ["migrations"]
    _sig, verdict = weighing.weigh([".agents/project/delivery/areas.json"], CLASSES, before,
                                   weighing.loosened(CLASSES, before, after), lost)
    assert verdict["class"]["id"] == "major" and "decision" in verdict["requires"]
    assert "walks what migrations asked" in verdict["why"]
    gone = weighing.loosened_areas(CLASSES, before, None)
    assert {a["id"] for a in gone} == {"migrations", "docs", "default_undo"}
    assert weighing.loosened_areas(CLASSES, after, before) == [], "tightening costs nothing"


def test_a_loosened_breadth_limit_walks_the_class_beyond_it():
    before, after = areas(max_areas={"standard": 1}), areas()
    lost = weighing.loosened_areas(CLASSES, before, after)
    _sig, verdict = weighing.weigh(["x"], CLASSES, before, weighing.loosened(CLASSES, before, after), lost)
    assert verdict["class"]["id"] == "normal"


def test_an_undo_cost_changed_to_a_word_nobody_declared_is_loosening():
    before = areas(("m", r"^m/", "irreversible"))
    after = areas(("m", r"^m/", "fatal"))
    assert any("undo irreversible -> fatal" in s for s in weighing.loosened(CLASSES, before, after))
    assert [a["id"] for a in weighing.loosened_areas(CLASSES, before, after)] == ["m"]


def test_an_area_record_held_on_a_card_raises_a_standard_change_to_a_card():
    # Found by an audit: a reversible area requiring review and a decision computed standard, owed
    # both, and the commit floor refused nothing.
    host = areas(("auth", r"^src/auth/", "reversible", {"requires": ["review", "decision"]}))
    cls, _sig, verdict = weigh(["src/auth/login.py"], host)
    assert cls == "normal" and "held on a card" in verdict["why"]
    assert any("owes a card" in s for s in refusals(["src/auth/login.py"], "feat: a\n", {}, host))


def test_a_classless_card_stands_at_least_where_its_uncertainty_asks():
    raised, why = weighing.card_floor(CLASSES, {"id": "x", "uncertainty": "chaotic"}, "normal")
    assert raised == "major" and "by its uncertainty chaotic" in why
    chaotic = {**CARD, "uncertainty": "chaotic"}
    said = refusals(["api/contracts/o.json"], "feat: o\n\nCard: orders\n", {"orders": chaotic})
    assert any("never passed one" in s for s in said), "a chaotic card walked a normal change without the bet"
    assert weighing.card_floor(CLASSES, {"id": "x", "class": "program", "uncertainty": "clear"}, "normal")[0] == "program"


def test_an_old_lowering_approval_cannot_be_replayed():
    entry = {"from": "major", "to": "normal", "at": "t", "by": "dev", "approved_by": "owner"}
    before = {"o.json": {"id": "o", "class": "major", "reshaped": [entry]}}
    replayed = {"o.json": {"id": "o", "class": "normal", "reshaped": [entry]}}
    assert "owner's door" in weighing.demotions(CLASSES, before, replayed)[0]


def test_a_blank_line_of_spaces_ends_a_paragraph_for_every_reader():
    message = "fix\n\nWork-Class: emergency\n   \nprose"
    assert weighing.trailers(message) == {}, "the hook read a trailer git's cleanup does not keep"


def test_a_declared_trailer_written_twice_is_refused():
    said = refusals(["db/migrations/1.sql"], "fix\n\nWork-Class: emergency\nWork-Class: major\n")
    assert any("written twice" in s for s in said)


def test_a_decision_is_what_its_front_matter_says_never_a_line_of_its_body():
    from types import SimpleNamespace
    import workclass
    files = {"d.md": "---\nkind: decision\n---\n# d\n", "n.md": "---\ntitle: notes\n---\nkind: decision\n",
             "open.md": "---\nkind: decision\n"}
    ctx = SimpleNamespace(workspace=SimpleNamespace(exists=files.__contains__, read_text=files.__getitem__),
                          enabled_capabilities=lambda: [])
    decided = workclass.decided(ctx)
    holder = {"field": "origin", "kind_of_record": "decision"}
    assert decided({"origin": {"ref": "d.md"}}, holder)
    assert not decided({"origin": {"ref": "n.md"}}, holder), "a body line was read as front matter"
    assert not decided({"origin": {"ref": "open.md"}}, holder), "front matter that never closes is none"


def test_a_decision_is_the_hosts_own_never_a_vendored_kits():
    # Found by an audit: a card bet on the vendored kit's own ADR read as the host's ruling.
    from types import SimpleNamespace
    import workclass
    body = "---\nkind: decision\n---\n# d\n"
    files = {"docs/decisions/ADR-001.md": body, "platform/kits/agent-kit/docs/decisions/ADR-025.md": body}
    layout = SimpleNamespace(documents={"host_layout": {"entries": [
        {"path": "docs/decisions/", "kind": "dir", "holds": "decision"}, {"path": "docs/work/", "holds": "work-card"}]}})
    ctx = SimpleNamespace(workspace=SimpleNamespace(exists=files.__contains__, read_text=files.__getitem__),
                          enabled_capabilities=lambda: [layout])
    decided = workclass.decided(ctx)
    holder = {"field": "origin", "kind_of_record": "decision"}
    assert decided({"origin": {"ref": "docs/decisions/ADR-001.md"}}, holder)
    assert not decided({"origin": {"ref": "platform/kits/agent-kit/docs/decisions/ADR-025.md"}}, holder), \
        "another repository's decision is not this host's"


def test_proof_is_weighed_as_the_work_is():
    # The owner: a one-line change must not run every suite the repository has.
    host = areas(("migrations", r"^db/migrations/", "irreversible", {"proved_by": ["kit:test-db"]}),
                 ("web", r"^web/", "reversible", {"proved_by": ["kit:test-web"]}),
                 ("docs", r"^docs/", "reversible", {"proved_by": []}))
    assert weighing.proof_for(["web/app.ts"], CLASSES, host)[0] == ["kit:test-web"], "the web app's tests, no other"
    assert weighing.proof_for(["docs/guide.md"], CLASSES, host)[0] == [], "prose is proved by check alone"
    assert weighing.proof_for([], CLASSES, host) == ([], "nothing new to prove")
    heavy, why = weighing.proof_for(["db/migrations/1.sql"], CLASSES, host)
    assert heavy is None and "owes a decision is proved by everything" in why


def test_an_area_that_declares_no_proof_is_proved_by_everything_and_says_so():
    host = areas(("web", r"^web/", "reversible", {"proved_by": ["kit:test-web"]}), ("loose", r"^loose/", "reversible"))
    commands, why = weighing.proof_for(["loose/x.txt"], CLASSES, host)
    assert commands is None and "loose declare(s) no proof" in why
    commands, why = weighing.proof_for(["nowhere/x.txt"], CLASSES, host)
    assert commands is None and "(no area)" in why
    host["default_proved_by"] = []
    assert weighing.proof_for(["nowhere/x.txt", "web/a.ts"], CLASSES, host)[0] == ["kit:test-web"], \
        "a path no area claims is proved by the default"


def test_a_hosts_areas_are_drafted_from_the_modules_its_build_tool_declares():
    # Found by the foreign-project experiment: areas seeded empty weighed a UI string and the deploy
    # manifest alike, and proved both by nothing.
    import re
    import sys as _sys
    _sys.path.insert(0, str(KIT / "interpreters" / "verbs"))
    import areas as areas_verb

    mapdoc = {"id": "a-build-tool-modules", "path": "build.json", "pointer": "modules", "path_field": "path",
              "proof": "tool:test-{id}", "declarations": [r"^build\.json$", "^ops/"], "declarations_proof": "tool:validate"}
    drafted = areas_verb.drafted([(mapdoc, {"web": {"path": "web"}, "api": {"path": "."}})],
                                 {"tool:test-web", "tool:validate"}, scale=[r["id"] for r in __import__("json").loads((Path(__file__).resolve().parents[2] / "kit" / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))["undo"]], drafts=__import__("json").loads((Path(__file__).resolve().parents[2] / "kit" / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))["drafted_areas"])
    by = {a["id"]: a for a in drafted}
    assert by["module-web"]["proved_by"] == ["tool:test-web"] and by["module-web"]["paths"] == "^web/"
    assert "proved_by" not in by["module-api"], "a module whose command nobody vouches is proved by everything"
    assert by["a-build-tool-modules-declarations"]["undo"] == "costly"
    assert by["prose"]["proved_by"] == []
    root = re.compile(by["module-api"]["paths"])
    assert root.search("src/main/java/App.java") and not root.search("web/src/main.tsx")
    assert not root.search("ops/deploy/targets.json") and not root.search("docs/guide.md")
    host = {"schema_version": 1, "default_undo": "reversible", "max_areas": {}, "areas": drafted}
    ui = weighing.weigh(["web/src/main.tsx"], CLASSES, host)[1]["class"]["id"]
    deploy = weighing.weigh(["ops/deploy/targets.json"], CLASSES, host)[1]["class"]["id"]
    assert ui != deploy, "a UI string and the deploy manifest no longer weigh the same"
    assert weighing.proof_for(["web/src/main.tsx"], CLASSES, host)[0] == ["tool:test-web"]


def test_a_dropped_feed_is_loosening():
    before = areas(("api", r"^api/", "costly", {"feeds": ["web"]}), ("web", r"^web/", "reversible"))
    after = areas(("api", r"^api/", "costly"), ("web", r"^web/", "reversible"))
    assert weighing.loosened(CLASSES, before, after) == ["area api no longer feeds web"]


def test_a_decision_owed_by_work_in_flight_keeps_its_kinds_shape_and_a_landed_one_is_not_reopened(monkeypatch):
    # ADR-024 amendment 1: the shape is the vocabulary's (data); it holds the work still being done.
    from types import SimpleNamespace
    import workclass
    shape = {"sections": [{"says": "the decision", "names": ["decision"]},
                          {"says": "the sources weighed", "names": ["source"], "entries_at_least": 1}]}
    vocabulary = SimpleNamespace(documents={"record_keeping": {"kinds": [{"id": "decision", "shape": shape}]}})
    files = {"short.md": "---\nkind: decision\n---\n# d\n## Decision\nOne queue.\n",
             "whole.md": "---\nkind: decision\n---\n# d\n## Decision\nOne queue.\n## Sources\n- RFC 9110\n"}
    ctx = SimpleNamespace(workspace=SimpleNamespace(exists=files.__contains__, read_text=files.__getitem__),
                          enabled_capabilities=lambda: [vocabulary])
    monkeypatch.setattr(workclass, "declarations", lambda _ctx: ({"working_states": ["in-flight", "verified"]}, {}))
    decided = workclass.decided(ctx)
    holder = {"field": "origin", "kind_of_record": "decision"}
    short = {"id": "q", "state": "in-flight", "origin": {"ref": "short.md"}}
    assert not decided(short, holder)
    assert decided.missing["q"] == ("short.md", ["the sources weighed"])
    assert decided({"id": "w", "state": "in-flight", "origin": {"ref": "whole.md"}}, holder)
    assert decided(dict(short, state="landed"), holder), "a decision a card landed on was held to a later rule"
