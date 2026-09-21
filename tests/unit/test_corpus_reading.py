"""Unit: the corpus READING and the two gates that report on it (ADR-019 decisions 1, 2, 7; S2a).

What is proved here is the RESOLUTION and the two reports over it, against the declarations the
kit actually ships: the gate rows are read out of the knowledge capability by id, the vocabulary
out of the governance document that owns it, and the gate functions out of the same discovery
`check` uses. Nothing here restates a class, a plane or an authority state -- every value under
test is derived from a ROW (`place_may_declare`, `place_default`, `binding_rank`), so a test that
went on passing after a word was renamed cannot be written in this file.

The walk, in the order ADR-019 decides it:

  1. a place CONFERS a class on a resident that declares none -- and the reading says the class
     came from the place, never from the artifact;
  2. a resident self-declaring above its place's ceiling is refused BY NAME;
  3. a resident self-declaring the state no place may confer is ACCEPTED -- the ceiling caps the
     place, and the state no place may name is outside its jurisdiction;
  4. two such artifacts owning one topic id are refused;
  5. a succession naming a document that does not exist, and one stated at a single end, are both
     refused;
  6. a host with no corpus map is GREEN and says what it therefore did not read;
  7. a document whose declaration cannot be read is NAMED, never counted as one that said nothing;
  8. the `where` filter: the ceiling refusal is a DECLARATION, and it catches a place capping with
     the one state no place may declare.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import corpus  # noqa: E402
import declared  # noqa: E402
import gatekinds  # noqa: E402
from manifest import Manifest  # noqa: E402
from workspace import Workspace  # noqa: E402

MANIFEST = Manifest(KIT)
KINDS = gatekinds.registry()

#: The capability that declares the corpus map readable, and the one that owns the words. Found by
#: what they DECLARE, never by a name spelled here.
CORPUS_MAPS = next((c, i) for c in MANIFEST.capabilities for i in c.installs
                   if i.get("validates") == "corpus-map")
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")

#: The three gate rows this slice ships, each read from the declaration that carries it.
GATES = {g["id"]: g for c in MANIFEST.capabilities for g in c.gates}
CENSUS = next(g for g in GATES.values() if g["kind"] == "artifact-classified")
CLAIMS = next(g for g in GATES.values() if g["kind"] == "authority-declared")
VOCABULARY_GATE = next(g for g in GATES.values() if g["id"] == "FF-CORPUS-VOCABULARY")


# -- the words, read from the rows that declare them ------------------------------------------
def _authorities() -> list:
    return VOCABULARY["authorities"]


def _top() -> str:
    """The most binding state the vocabulary declares -- the one a second claimant can
    contradict, which is why it is the one that must say what it OWNS."""
    return max(_authorities(), key=lambda a: a[corpus.RANK])["id"]


def _default() -> dict:
    return next(a for a in _authorities() if a[corpus.IS_DEFAULT])


def _below_default() -> dict:
    """A state binding strictly less than the default ceiling -- what a place caps with when it
    means that nothing resident there may be current."""
    return next(a for a in sorted(_authorities(), key=lambda r: -r[corpus.RANK])
                if a[corpus.RANK] < _default()[corpus.RANK])


def _class() -> str:
    return VOCABULARY["kinds"][0]["id"]


# -- a host, and a context over it --------------------------------------------------------------
class Only:
    """A real capability with only the installs a test's subject needs. Its DOCUMENTS and its
    gate rows are the kit's own -- what is narrowed is the set of host files the reading must
    find, never a declaration under test."""

    def __init__(self, capability, installs) -> None:
        self.id, self.documents, self.raw = capability.id, capability.documents, capability.raw
        self.installs = installs
        self.gates = capability.gates


class Ctx:
    """The plumbing a gate is handed: a rooted workspace, the kit's manifest, and the set of
    capabilities that are enabled. Nothing else of a real run reaches these gates."""

    def __init__(self, root: Path) -> None:
        self.workspace = Workspace(root)
        self.manifest = MANIFEST
        owner, install = CORPUS_MAPS
        self._enabled = [Only(c, [install] if c.id == owner.id else [])
                         for c in MANIFEST.capabilities
                         if c.id in {owner.id} | {c2.id for c2 in MANIFEST.capabilities
                                                  if "record_keeping" in c2.documents}]

    def enabled_capabilities(self):
        return self._enabled


_TRASH: list = []


def _host(places: list, documents: dict, mapped: bool = True) -> Ctx:
    """A scratch host: a corpus map (unless the case is a host without one) and its documents."""
    root = Path(tempfile.mkdtemp(prefix="corpus-"))
    _TRASH.append(root)
    if mapped:
        target = root / CORPUS_MAPS[1]["target"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "map.json").write_text(
            json.dumps({"schema_version": 1, "id": "fixture", "places": places}, indent=2) + "\n",
            encoding="utf-8", newline="\n")
    for rel, text in documents.items():
        whole = root / rel
        whole.parent.mkdir(parents=True, exist_ok=True)
        whole.write_text(text, encoding="utf-8", newline="\n")
    return Ctx(root)


def teardown_module(_module) -> None:
    for path in _TRASH:
        shutil.rmtree(path, ignore_errors=True)


def _front(**fields) -> str:
    lines = [corpus.FENCE]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append(corpus.FENCE)
    return "\n".join(lines) + "\n\n# a document\n"


def _census(ctx) -> list:
    return KINDS[CENSUS["kind"]](ctx, CENSUS["params"])


def _claims(ctx) -> list:
    return KINDS[CLAIMS["kind"]](ctx, CLAIMS["params"])


def _named(findings: list, path: str) -> list:
    return [f for f in findings if f.startswith(f"{path}:")]


# --------------------------------------------------------------------------------------------
# 1. A place confers a class; it never supplies authority, and the reading says which is which.
# --------------------------------------------------------------------------------------------
def test_a_place_confers_a_class_on_a_resident_that_declares_none(capsys):
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class()}],
        {"docs/quiet.md": "# a document that says nothing about itself\n"},
    )
    reading = corpus.read(ctx, CENSUS["params"])
    resident = reading.residents[0]
    found, source = reading.class_of(resident)
    authority, from_where = reading.authority_of(resident)
    print(f"{resident.path}: class {found!r} from {source!r}; authority {authority!r} "
          f"from {from_where!r}")

    assert (found, source) == (_class(), corpus.PLACE), "the place did not confer, or it lied"
    assert (authority, from_where) == (None, None), (
        "a place supplied AUTHORITY -- a location became a reason to believe something"
    )
    assert resident.declares_nothing, "a conferred class was read back as a self-declaration"

    assert _census(ctx) == [], "a census reported a DEFECT where it had only a reading to state"
    said = capsys.readouterr().out
    assert "1 declared nothing" in said and "are classed by the place they reside in" in said


# --------------------------------------------------------------------------------------------
# 2-3. The ceiling caps the states a place may name, and nothing else.
# --------------------------------------------------------------------------------------------
def test_a_resident_declaring_above_its_places_ceiling_is_refused_by_name(capsys):
    ceiling = _below_default()
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: ceiling["id"]}],
        {"docs/reaching.md": _front(**{corpus.AUTHORITY: _default()["id"]}),
         "docs/content.md": _front(**{corpus.AUTHORITY: ceiling["id"]})},
    )
    findings = _claims(ctx)
    print("\n".join(findings))
    assert len(_named(findings, "docs/reaching.md")) == 1, findings
    assert ceiling["id"] in findings[0] and _default()["id"] in findings[0]
    assert _named(findings, "docs/content.md") == [], (
        "a resident declaring exactly its ceiling was refused"
    )


def test_the_most_binding_claim_needs_a_place_that_permits_it_and_a_word_of_its_own(capsys):
    """Two declarations, not one. A place where the most binding state is legitimate SAYS so with
    its ceiling, and the artifact still has to claim it -- neither alone is enough, and the place
    alone is never enough at all. Under the DEFAULT ceiling the same claim is refused, which is
    how a place demotes by location instead of a filename promoting by accident
    (ADR-019 amendment 1)."""
    owned = {corpus.AUTHORITY: _top(), corpus.OWNS: "the-shape-of-x"}
    permitted = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: _top()}],
        {"docs/settled.md": _front(**owned)},
    )
    assert _claims(permitted) == [], "a place that permits the top state still refused it"

    ordinary = _host([{corpus.PATH: "docs/", corpus.HOLDS: _class()}],
                     {"docs/settled.md": _front(**owned)})
    findings = _claims(ordinary)
    print(chr(10).join(findings))
    assert len(_named(findings, "docs/settled.md")) == 1, (
        "the default ceiling let the most binding claim through -- a place that never says so "
        "has granted the strongest state in the vocabulary by silence"
    )


def test_a_top_authority_claim_that_owns_nothing_is_refused(capsys):
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: _top()}],
        {"docs/unowned.md": _front(**{corpus.AUTHORITY: _top()})},
    )
    findings = _claims(ctx)
    print("\n".join(findings))
    assert len(_named(findings, "docs/unowned.md")) == 1, findings
    assert corpus.OWNS in findings[0]


def test_two_artifacts_owning_one_topic_are_refused_and_both_are_named(capsys):
    claim = {corpus.AUTHORITY: _top(), corpus.OWNS: "the-shape-of-x"}
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: _top()}],
        {"docs/first.md": _front(**claim), "docs/second.md": _front(**claim)},
    )
    findings = _claims(ctx)
    print("\n".join(findings))
    assert len(findings) == 1, findings
    assert "docs/first.md" in findings[0] and "docs/second.md" in findings[0]
    assert "the-shape-of-x" in findings[0]


# --------------------------------------------------------------------------------------------
# 5. A succession is stated at both ends, or it is not stated.
# --------------------------------------------------------------------------------------------
def test_a_succession_that_dangles_and_one_stated_at_a_single_end_are_both_refused(capsys):
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class()}],
        {
            "docs/dangling.md": _front(**{corpus.SUPERSEDES: "docs/never-written.md"}),
            "docs/one-way.md": _front(**{corpus.SUPERSEDES: "docs/silent.md"}),
            "docs/silent.md": "# replaced, and it does not know it\n",
            "docs/new.md": _front(**{corpus.SUPERSEDES: "docs/old.md"}),
            "docs/old.md": _front(**{corpus.SUPERSEDED_BY: "docs/new.md"}),
        },
    )
    findings = _claims(ctx)
    print("\n".join(findings))
    assert len(_named(findings, "docs/dangling.md")) == 1, findings
    assert "not a document of this host" in _named(findings, "docs/dangling.md")[0]
    assert len(_named(findings, "docs/one-way.md")) == 1, findings
    assert "does not answer" in _named(findings, "docs/one-way.md")[0]
    assert _named(findings, "docs/new.md") == [] and _named(findings, "docs/old.md") == [], (
        "a succession stated at both ends was refused"
    )


# --------------------------------------------------------------------------------------------
# 6. Lazy materialization: no map is green, and it SAYS what it did not read.
# --------------------------------------------------------------------------------------------
def test_a_host_with_no_corpus_map_is_green_and_says_it_read_nothing(capsys):
    ctx = _host([], {"docs/anything.md": "# unread\n"}, mapped=False)
    assert _census(ctx) == [], "an absent corpus map was reported as a defect rather than read"
    census_said = capsys.readouterr().out
    assert "NOTHING WAS READ" in census_said and "declares no corpus map" in census_said
    assert _claims(ctx) == [], (
        "a host that mapped nothing was reported as having an authority defect -- it cannot have "
        "one: no place, no resident, no claim"
    )
    assert "NOTHING WAS READ" in capsys.readouterr().out
    assert corpus.read(ctx, CENSUS["params"]).unmapped


def test_a_declared_place_that_holds_no_document_is_not_reported_as_a_clean_corpus(capsys):
    ctx = _host([{corpus.PATH: "docs/", corpus.HOLDS: _class()}], {"docs/keep.txt": "not a document\n"})
    assert _census(ctx) == []
    assert "NOTHING WAS READ" in capsys.readouterr().out


# --------------------------------------------------------------------------------------------
# 7. A declaration that cannot be read is NAMED.
# --------------------------------------------------------------------------------------------
def test_a_declaration_that_cannot_be_read_is_named_and_not_counted_as_silence(capsys):
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class()}],
        {
            "docs/torn.md": f"{corpus.FENCE}\n{corpus.KIND}: {_class()}\n\n# never closed\n",
            "docs/invented.md": _front(**{"a_field_nobody_declared": "x"}),
        },
    )
    findings = _census(ctx)
    said = capsys.readouterr().out
    print(said)
    for path in ("docs/torn.md", "docs/invented.md"):
        named = _named(findings, path)
        assert len(named) == 1 and "UNREADABLE" in named[0], (path, findings)
    assert "0 declared nothing" in said, (
        "an unreadable document was counted as one that declared nothing -- two states, one count"
    )


# --------------------------------------------------------------------------------------------
# 8. `among.where`: the ceiling refusal is a DECLARATION, and it bites.
# --------------------------------------------------------------------------------------------
def test_the_declared_filter_narrows_a_referent_set_to_the_rows_a_flag_marks(capsys):
    """`among.where` exists so that a referent set can be A SUBSET of a declared list without any
    gate module holding the rule. It ships with NO user in this slice: the ceiling reference that
    first asked for it was dropped by ADR-019 amendment 1, and its next user is the entry set of
    the reachability reading. So it is proved here directly, against rows this test declares --
    machinery with a named next user, never a capability shipped on a promise nobody wrote down."""
    rows = [{"id": "one", "flagged": True}, {"id": "two", "flagged": False},
            {"id": "three", "flagged": True}]
    selected = [row["id"] for row in declared.matching(rows, {"field": "flagged", "equals": True})]
    print(f"selected {selected} of {[r['id'] for r in rows]}")

    assert selected == ["one", "three"], selected
    assert declared.matching(rows, None) == rows, "no filter narrowed the set"
    assert declared.matching(rows, {"field": "flagged", "equals": "True"}) == [], (
        "the filter compared a string to a boolean and called them equal -- a value that matches "
        "across types is how a declaration silently selects rows nobody meant"
    )


def test_a_place_capping_with_a_word_no_vocabulary_row_declares_is_refused(capsys):
    """A ceiling is read by comparing RANKS, and a word with no row has no rank -- so an unknown
    ceiling would fall back to the default while the row went on reading as a cap somebody wrote.
    Capping with the MOST BINDING state is legitimate, and the second half proves it: a place may
    LOWER a claim and may never RAISE one, and that holds at every rank (ADR-019 amendment 1)."""
    invented = "a-word-no-vocabulary-row-declares"
    ctx = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: invented}],
        {"docs/a.md": "# a document\n"},
    )
    findings = KINDS[VOCABULARY_GATE["kind"]](ctx, VOCABULARY_GATE["params"])
    print(chr(10).join(findings))
    assert len(findings) == 1 and invented in findings[0], findings

    topped = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: _top()}],
        {"docs/a.md": "# a document\n"},
    )
    assert KINDS[VOCABULARY_GATE["kind"]](topped, VOCABULARY_GATE["params"]) == [], (
        "a place declaring the most binding ceiling was refused -- then no place could ever hold "
        "a settled answer, and the state would be unreachable rather than merely guarded"
    )

    fine = _host(
        [{corpus.PATH: "docs/", corpus.HOLDS: _class(), corpus.CEILING: _default()["id"]}],
        {"docs/a.md": "# a document\n"},
    )
    assert KINDS[VOCABULARY_GATE["kind"]](fine, VOCABULARY_GATE["params"]) == [], (
        "a place capping with a state it is permitted to name was refused"
    )
