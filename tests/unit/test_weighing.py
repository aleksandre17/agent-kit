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


def refusals(paths, message, cards=None, host=HOST):
    return weighing.commit_refusals(CLASSES, weigh(paths, host)[2], message, cards or {})


CARD = {"id": "orders", "state": "in-flight"}


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
    assert len(said) == 1 and "re-shape the card" in said[0]
    assert refusals(["db/migrations/1.sql"], "feat: m\n\nCard: orders\n", {"orders": {**CARD, "class": "major"}}) == []


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
