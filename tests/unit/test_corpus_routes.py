"""Unit: the corpus ROUTE GRAPH and the two gates that stand on it (ADR-019 decisions 5, 6; S2b).

What is proved here is the graph and the two readings over it, against the declarations the kit
actually ships. Nothing in this file spells a marker, an authority word or a flag: the obligation
text a fixture document carries is the `proves` line of a declared marker ROW, the lookalike it
must tolerate is that row's `admits` line, the authority an index mis-states is read from the
authority vocabulary, and the flag that makes a place an ENTRY is read out of the gate's own
declared filter. A test that went on passing after a word was renamed cannot be written here
(Cardinal IV).

The host harness -- the scratch tree, the context, the front-matter writer -- is the one built for
S2a and is imported rather than copied: two scratch hosts would be two answers to *what a host
under test looks like*, and they would agree until one of them was fixed (Cardinal III).

The walk, in the order the invariants decide it:

  1. a document carrying an obligation and reachable from an entry is REPORTED, never refused;
  2. one carrying an obligation and reachable from nothing is NAMED, with the marks it carries;
  3. one reachable from nothing that owes nothing is not a finding and is not named;
  4. a lookalike the vocabulary swears it tolerates is not an obligation;
  5. `indexed_by` is an edge: a resident nothing links is reached through its place's index;
  6. a mark that fails its own calibration is REFUSED, and the four the kit ships all pass;
  7. an index that omits a resident, one that carries a row for a document that is not there, and
     one whose row states an authority the artifact does not -- all three refused;
  8. a place that declares no index is NOT CHECKED, and says so;
  9. a host with no corpus map is green under both gates and says what it did not read.
"""

from __future__ import annotations

import test_corpus_reading as s2a  # the S2a harness: one home for the scratch host

import corpus  # noqa: E402
import declared  # noqa: E402
import routes  # noqa: E402

#: The two gate rows this slice ships, each read from the declaration that carries it.
GATES = {g["id"]: g for c in s2a.MANIFEST.capabilities for g in c.gates}
ROUTED = next(g for g in GATES.values() if g["kind"] == "obligation-reachable")
INDEXED = next(g for g in GATES.values() if g["kind"] == "index-complete")

#: The marks the kit ships, read from the governance document that owns them.
MARKS = next(c.documents[d["id"]] for c in s2a.MANIFEST.capabilities
             for d in c.raw.get("documents", []) if d["validates"] == "obligation-markers")

#: What makes a place a ROOT, read out of the gate's own declared filter rather than spelled here.
FLAG = ROUTED["params"][corpus.ROOTS][declared.FIELD]
MARKED = ROUTED["params"][corpus.ROOTS][declared.EQUALS]

ENTRY = {corpus.PATH: "steering/", corpus.HOLDS: s2a._class(), FLAG: MARKED}
PLACE = {corpus.PATH: "docs/", corpus.HOLDS: s2a._class()}


def _owing() -> str:
    """A line one declared mark swears it matches -- an obligation, in the vocabulary's own words."""
    return MARKS[ROUTED["params"][routes.MARKERS][corpus.LIST]][0][routes.PROVES]


def _lookalike() -> str:
    """A line that same mark swears it tolerates."""
    return MARKS[ROUTED["params"][routes.MARKERS][corpus.LIST]][0][routes.ADMITS]


def _routed(ctx) -> list:
    return s2a.KINDS[ROUTED["kind"]](ctx, ROUTED["params"])


def _indexed(ctx) -> list:
    return s2a.KINDS[INDEXED["kind"]](ctx, INDEXED["params"])


def _unrouted(said: str) -> list:
    return [line.split("UNROUTED: ")[1].split(" -- ")[0]
            for line in said.split("\n") if "UNROUTED: " in line]


# --------------------------------------------------------------------------------------------
# 1-4. Reachability is a MEASUREMENT: it names what owes and cannot be reached, and nothing else.
# --------------------------------------------------------------------------------------------
def test_an_obligation_no_entry_reaches_is_named_and_one_an_entry_reaches_is_not(capsys):
    ctx = s2a._host(
        [ENTRY, PLACE],
        {
            "steering/capsule.md": "# where the work is steered\n\n[the routed one](../docs/routed.md)\n",
            "docs/routed.md": f"# reached from an entry\n\n{_owing()}\n",
            "docs/stranded.md": f"# reached by nothing\n\n{_owing()}\n",
            "docs/inert.md": f"# reached by nothing, owing nothing\n\n{_lookalike()}\n",
        },
    )
    findings = _routed(ctx)
    said = capsys.readouterr().out
    print(said)

    assert findings == [], (
        "a reachability READING returned a defect. An obligation that no route reaches is legal on "
        "the day this ships -- the verdict is a budget's, and a gate that fails on a legal state "
        "teaches its reader to ignore it"
    )
    assert _unrouted(said) == ["docs/stranded.md"], _unrouted(said)
    assert "docs/inert.md" not in said, (
        "a document that is reachable from nothing and owes nothing was named. It is not a finding "
        "and not a line of output: an unlinked reference is inert"
    )
    assert "3 document(s) carry" not in said, "a lookalike the vocabulary admits was counted as owed"
    assert "2 document(s) carry 2 live obligation" in said, said
    assert "1 document(s) carry an obligation that NO route" in said, said


def test_depth_is_reported_from_the_declared_entries_and_never_gated(capsys):
    ctx = s2a._host(
        [ENTRY, PLACE],
        {
            "steering/capsule.md": "# entry\n\n[one hop](../docs/one.md)\n",
            "docs/one.md": "# one hop out\n\n[two hops](two.md)\n",
            "docs/two.md": f"# two hops out\n\n{_owing()}\n",
        },
    )
    assert _routed(ctx) == [], "a distance was turned into a verdict"
    said = capsys.readouterr().out
    print(said)
    assert "(hops:documents) 0:1, 1:1, 2:1" in said, said
    assert "walked from 1 document(s) resident in 1 declared entry place(s)" in said, said
    assert _unrouted(said) == [], "a document two hops from an entry was called unreachable"


def test_a_resident_nothing_links_is_reached_through_the_index_its_place_declares(capsys):
    """`indexed_by` is an EDGE, and it is the one that makes the mechanism affordable: a host
    routes a whole place by writing one row about it, instead of linking a thousand documents."""
    place = dict(PLACE, **{corpus.INDEX: "docs/register.md"})
    ctx = s2a._host(
        [ENTRY, place],
        {
            "steering/capsule.md": "# entry\n\n[the register](../docs/register.md)\n",
            "docs/register.md": "# a register that links nothing\n",
            "docs/owing.md": f"# linked by nobody, indexed by the place\n\n{_owing()}\n",
        },
    )
    assert _routed(ctx) == []
    said = capsys.readouterr().out
    print(said)
    assert _unrouted(said) == [], (
        "a resident of an indexed place was unreachable -- the index edge was not walked, and a "
        "host would have to link every document by hand to route any of them"
    )


def test_a_place_that_no_row_marks_as_an_entry_is_not_a_root(capsys):
    """The filter is the mechanism: a graph whose roots are every place has no unreachable node
    and measures nothing. This is `matching`'s named user -- one field, one value, read from the
    declaration."""
    ctx = s2a._host(
        [PLACE],
        {"docs/alone.md": f"# nothing declares an entry\n\n{_owing()}\n"},
    )
    assert _routed(ctx) == []
    said = capsys.readouterr().out
    print(said)
    assert _unrouted(said) == ["docs/alone.md"]
    assert "NO ENTRY WAS DECLARED" in said, (
        "a walk from zero roots reported every document as unreachable without saying that the map "
        "declares no entry -- a statement about the corpus made out of a hole in the map"
    )
    assert declared.matching([PLACE, ENTRY], ROUTED["params"][corpus.ROOTS]) == [ENTRY], (
        "the declared root filter selected a place no row marks"
    )


def test_what_is_an_edge_and_what_only_looks_like_one(capsys):
    """The graph is built from links that RESOLVE, and from nothing that merely looks like one.
    Measured rather than assumed (Cardinal VII): an example inside a fenced block, another
    machine's address, a path this host does not hold, and a bare mention in prose are each a
    reason a corpus could read better connected than it is."""
    ctx = s2a._host(
        [ENTRY, PLACE],
        {
            "steering/capsule.md": (
                "# entry\n\n"
                "[with a fragment](../docs/fragment.md#a-heading)\n"
                "[defined below][row]\n\n"
                "[row]: ../docs/defined.md\n\n"
                "```\n[an example](../docs/fenced.md)\n```\n\n"
                "[another machine](https://example.invalid/docs/remote.md)\n"
                "[outside this host](../../elsewhere.md)\n"
                "and ../docs/mentioned.md written as prose\n"
            ),
            "docs/fragment.md": "# reached, fragment and all\n",
            "docs/defined.md": "# reached through a reference definition\n",
            "docs/fenced.md": f"# an example is not a route\n\n{_owing()}\n",
            "docs/mentioned.md": f"# a mention is not a link\n\n{_owing()}\n",
        },
    )
    assert _routed(ctx) == []
    said = capsys.readouterr().out
    print(said)
    assert "joined by 2 edge(s)" in said, said
    assert sorted(_unrouted(said)) == ["docs/fenced.md", "docs/mentioned.md"], _unrouted(said)
    assert "2 link(s) named nothing this reading reaches" in said, (
        "a link this reading cannot resolve was dropped instead of counted -- a graph that forgets "
        "what it could not read reports a corpus better connected than it is"
    )


# --------------------------------------------------------------------------------------------
# 6. A mark is held to its own calibration before it reads anything.
# --------------------------------------------------------------------------------------------
def test_every_mark_the_kit_ships_matches_what_it_swears_it_matches(capsys):
    marks, findings = routes.calibrated(MARKS[ROUTED["params"][routes.MARKERS][corpus.LIST]])
    print(f"{len(marks)} mark(s) calibrated; {findings}")
    assert findings == [], findings
    assert len(marks) == len(MARKS[ROUTED["params"][routes.MARKERS][corpus.LIST]])


def test_a_mark_that_fails_its_own_calibration_is_refused_in_both_directions(capsys):
    rows = MARKS[ROUTED["params"][routes.MARKERS][corpus.LIST]]
    blind = dict(rows[0], **{routes.PATTERN: "a pattern this line cannot contain"})
    crying = dict(rows[0], **{routes.PATTERN: "."})
    marks, findings = routes.calibrated([blind, crying])
    print("\n".join(findings))

    assert marks == [], "a mark that failed its calibration was allowed to read a corpus"
    assert len(findings) == 2, findings
    assert routes.PROVES in findings[0] and routes.ADMITS in findings[1], findings


# --------------------------------------------------------------------------------------------
# 7-8. An index is decided in BOTH directions, and a place that promised none is not checked.
# --------------------------------------------------------------------------------------------
def _index_host(rows: str):
    """A place with an index, a place with none, and three residents the index must answer for."""
    return s2a._host(
        [dict(PLACE, **{corpus.INDEX: "docs/register.md", corpus.CEILING: s2a._top()}),
         {corpus.PATH: "guides/", corpus.HOLDS: s2a._class()}],
        {
            "docs/register.md": f"# the register of this place\n\n{rows}",
            "docs/listed.md": "# in the register\n",
            "docs/omitted.md": "# not in the register\n",
            "docs/quiet.md": "# in the register, declaring nothing\n",
            "guides/unindexed.md": "# a place that promised no index\n",
        },
    )


def test_an_index_is_refused_for_what_it_omits_for_what_it_invents_and_for_what_it_mis_states(capsys):
    top = s2a._top()
    ctx = _index_host(
        "- [the listed one](listed.md)\n"
        "- [one that was never written](never-written.md)\n"
        f"- [the quiet one](quiet.md) -- {top}\n"
    )
    findings = _indexed(ctx)
    said = capsys.readouterr().out
    print(said + "\n".join(findings))

    assert len(findings) == 3, findings
    assert any("does not link docs/omitted.md" in f for f in findings), (
        "an index missing its subject passed -- a one-directional check is the failure mode this "
        "invariant exists for"
    )
    assert any("never-written.md" in f and "nothing is there" in f for f in findings), findings
    assert any("docs/quiet.md" in f and top in f and "states" in f for f in findings), findings
    assert all(f.startswith("docs/register.md:") for f in findings), (
        "a defect of an index was charged to the document it failed to list"
    )
    assert "1 place(s) declare no index and are NOT CHECKED" in said, said
    assert "0 link(s) written by an index point outside the place" in said, (
        "the gate did not state what it declined to judge; a reading that names only what it "
        "looked at reads exactly like a reading that looked at everything"
    )
    assert "guides/unindexed.md" not in said + "".join(findings), (
        "a place that declares no index was checked -- the invariant starts at zero or it bites on "
        "a legal state from the first day"
    )


def test_an_index_that_agrees_with_its_place_in_both_directions_is_green(capsys):
    ctx = _index_host(
        "- [the listed one](listed.md)\n"
        "- [the omitted one](omitted.md)\n"
        "- [the quiet one](quiet.md)\n"
    )
    assert _indexed(ctx) == [], "a complete index was refused"
    print(capsys.readouterr().out)


def test_an_index_the_map_promises_and_nobody_wrote_is_refused(capsys):
    ctx = s2a._host(
        [dict(PLACE, **{corpus.INDEX: "docs/never-written.md"})],
        {"docs/resident.md": "# a resident of a place whose index does not exist\n"},
    )
    findings = _indexed(ctx)
    print("\n".join(findings))
    assert len(findings) == 1 and "no document is there" in findings[0], findings


# --------------------------------------------------------------------------------------------
# 9. Lazy materialization: no map is green under both, and each SAYS what it did not read.
# --------------------------------------------------------------------------------------------
def test_a_host_with_no_corpus_map_is_green_under_both_gates_and_says_it_read_nothing(capsys):
    ctx = s2a._host([], {"docs/anything.md": f"# unread\n\n{_owing()}\n"}, mapped=False)

    assert _routed(ctx) == [], "an absent corpus map was read as an unrouted obligation"
    said = capsys.readouterr().out
    assert "NOTHING WAS READ" in said and "declares no corpus map" in said, said

    assert _indexed(ctx) == [], "an absent corpus map was read as an incomplete index"
    assert "NOTHING WAS READ" in capsys.readouterr().out


def test_a_declared_place_holding_no_document_is_not_read_as_a_routed_corpus(capsys):
    ctx = s2a._host([ENTRY], {"steering/keep.txt": "not a document\n"})
    assert _routed(ctx) == [] and _indexed(ctx) == []
    assert capsys.readouterr().out.count("NOTHING WAS READ") == 2
