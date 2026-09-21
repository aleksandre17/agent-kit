"""Unit: NAVIGATION as a PROJECTION -- the catalog and the routes page (ADR-019 decision 4; S4).

What is proved here is that two surfaces state what the declarations say, and say so honestly when
there is nothing to state. Nothing in this file spells a place, a plane, a class or an authority
word: the capability under test is found by the BLOCK it declares, its two pages by the installs
that carry them, the entry flag by the declared root filter of its own params, and every vocabulary
word by the row that declares it. A test that went on passing after a word was renamed cannot be
written here (Cardinal IV).

The host harness -- the scratch tree, the context, the map writer -- is the one built for S2a and is
imported rather than copied: two scratch hosts would be two answers to *what a host under test looks
like*, and they would agree until one of them was fixed (Cardinal III).

The walk:

  1. a host with a real corpus map: both pages render, every declared place is on the catalog, and
     the counts are the ones the census GATE reports -- the same sentence, word for word;
  2. a place whose class names no declared plane is still printed, because a row that vanishes from
     a catalog is the one defect a catalog may never have;
  3. the entries, their declared `read_when` and the depth distribution reach the routes page;
  4. a host that declares no corpus map: both pages render and SAY nothing was read -- an empty page
     and a page about an empty corpus are different propositions (Cardinal V);
  5. byte-reproducibility: rendered twice, identical bytes, no clock and no dict-order;
  6. a view declared with a resolver kind nothing answers for is REFUSED by name, never rendered as
     an empty section.
"""

from __future__ import annotations

import test_corpus_reading as s2a  # the S2a harness: one home for the scratch host

import corpus  # noqa: E402
import declared  # noqa: E402
import resolution  # noqa: E402
import template  # noqa: E402

#: The capability that resolves a reading into its view, found by the BLOCK it declares.
READER = next(c for c in s2a.MANIFEST.capabilities if c.raw.get(resolution.BLOCK))
SPEC = READER.raw[resolution.BLOCK][0]
PARAMS = SPEC[resolution.PARAMS]

#: Its projected pages, found by what they ARE -- a projection this capability installs.
PAGES = [i for i in READER.installs if i["class"] == "projection"]

#: What makes a place an ENTRY, read out of the declaration's own root filter.
FLAG = PARAMS[corpus.ROOTS][declared.FIELD]
MARKED = PARAMS[corpus.ROOTS][declared.EQUALS]

#: A word the vocabulary does not declare -- used only where the point IS that nothing declares it.
UNDECLARED = "a-class-no-vocabulary-row-declares"


def _view(ctx) -> dict:
    """The view model as the renderer builds it, narrowed to what these two pages read: the kit's
    version, and the reading claimed under the id the declaration gives it."""
    resolved = resolution.resolved_of(ctx, READER)
    assert len(resolved) == 1, "the capability under test resolves more than one reading"
    return {"kit_version": s2a.MANIFEST.version, resolved[0].spec[resolution.ID]: resolved[0].value}


def _rendered(ctx) -> dict:
    """Both pages, by their declared target, rendered exactly as `render` would render them."""
    view = _view(ctx)
    return {page["target"]: template.render(s2a.MANIFEST.payload_text(page["source"]), view)
            for page in PAGES}


def _page(pages: dict, holding: str) -> str:
    return next(text for target, text in pages.items() if holding in text)


# --------------------------------------------------------------------------------------------
# 1. A real map: every declared place is on the catalog, and the counts are the GATE's counts.
# --------------------------------------------------------------------------------------------
def test_every_declared_place_is_on_the_catalog_with_the_counts_the_gate_reports(capsys):
    places = [
        {corpus.PATH: "steering/", corpus.HOLDS: s2a._class(), FLAG: MARKED,
         corpus.READ_WHEN: ["resuming work"], corpus.INDEX: "steering/INDEX.md"},
        {corpus.PATH: "docs/", corpus.HOLDS: s2a._class(),
         corpus.WRITER: s2a.VOCABULARY["writers"][0]["id"],
         corpus.LIFECYCLE: s2a.VOCABULARY["lifecycles"][0]["id"],
         corpus.CEILING: s2a._below_default()["id"]},
    ]
    ctx = s2a._host(places, {
        "steering/INDEX.md": "# the index\n\n[the quiet one](../docs/quiet.md)\n",
        "docs/quiet.md": "# a document that says nothing about itself\n",
        "docs/spoken.md": s2a._front(**{corpus.AUTHORITY: s2a._below_default()["id"]}),
    })

    reading = corpus.read(ctx, PARAMS)
    s2a._census(ctx)
    said = capsys.readouterr().out
    pages = _rendered(ctx)
    catalog = _page(pages, "made of")

    assert len(pages) == 2, f"two pages are declared and {len(pages)} rendered"
    for place in places:
        assert place[corpus.PATH] in catalog, (
            f"the declared place {place[corpus.PATH]!r} is on no row of the catalog -- a row that "
            f"vanishes from a catalog is the defect a catalog may never have"
        )
    assert reading.subject() in catalog and reading.subject() in said, (
        "the catalog and the census gate do not state the SAME reading, word for word -- two "
        "readings of one corpus that will agree until one of them is fixed"
    )
    assert f"**{len(reading.spoke)}** declared their own class" in catalog
    assert f"**{len(reading.undeclared)}** declared nothing" in catalog
    assert f"{len(reading.spoke)} declared their own class" in said

    # What the map DECLARED about a place, and what it left out, are two different sentences.
    assert s2a.VOCABULARY["writers"][0]["id"] in catalog
    assert "not declared by this row" in catalog, (
        "a field no row declares rendered as a blank -- which a reader reads as a zero"
    )
    assert s2a._below_default()["id"] in catalog and corpus.PATH not in catalog


# --------------------------------------------------------------------------------------------
# 2. A row is never dropped for having nowhere to go.
# --------------------------------------------------------------------------------------------
def test_a_place_whose_class_names_no_declared_plane_is_printed_and_not_dropped():
    ctx = s2a._host(
        [{corpus.PATH: "docs/", corpus.HOLDS: UNDECLARED}],
        {"docs/quiet.md": "# a document\n"},
    )
    catalog = _page(_rendered(ctx), "made of")

    assert "Outside every declared plane" in catalog and UNDECLARED in catalog, (
        "a place whose class names no declared plane was filed under a guess or dropped"
    )


# --------------------------------------------------------------------------------------------
# 3. The routes page states the declared entries, their triggers and the distances walked.
# --------------------------------------------------------------------------------------------
def test_the_routes_page_states_the_declared_entries_their_triggers_and_the_depths():
    trigger = "a task arrives asking where the work stands"
    ctx = s2a._host(
        [{corpus.PATH: "steering/", corpus.HOLDS: s2a._class(), FLAG: MARKED,
          corpus.READ_WHEN: [trigger]},
         {corpus.PATH: "docs/", corpus.HOLDS: s2a._class(), corpus.READ_WHEN: ["asked about docs"]}],
        {"steering/capsule.md": "# steering\n\n[onward](../docs/reached.md)\n",
         "docs/reached.md": "# reached at one hop\n",
         "docs/alone.md": "# reached by nothing\n"},
    )
    routes = _page(_rendered(ctx), "reaches what they need")

    assert trigger in routes and "asked about docs" in routes, (
        "a declared retrieval trigger is missing from the page projected from it"
    )
    assert "1 hop(s) from an entry** — 1 document(s)" in routes, (
        "the depth distribution the graph computes did not reach the page"
    )
    assert "1 are reached by nothing" in routes


# --------------------------------------------------------------------------------------------
# 4. A host with no corpus map: the pages render, and they say what was not read.
# --------------------------------------------------------------------------------------------
def test_a_host_with_no_corpus_map_gets_both_pages_and_they_say_nothing_was_read():
    ctx = s2a._host([], {"docs/quiet.md": "# a document\n"}, mapped=False)
    pages = _rendered(ctx)
    absent = corpus.read(ctx, PARAMS).nothing_read()

    assert len(pages) == 2, "lazy materialization failed: an unmapped host got fewer than two pages"
    for target, text in pages.items():
        assert absent in text, (
            f"{target} does not carry the reading's own words for what it did not read -- an empty "
            f"catalog and a catalog of an unmapped corpus are different propositions"
        )
        assert "READ 0 document(s)" not in text, f"{target} reported a green zero it never read"


# --------------------------------------------------------------------------------------------
# 5. Rendered twice, identical bytes.
# --------------------------------------------------------------------------------------------
def test_both_pages_are_byte_reproducible():
    ctx = s2a._host(
        [{corpus.PATH: "steering/", corpus.HOLDS: s2a._class(), FLAG: MARKED},
         {corpus.PATH: "docs/", corpus.HOLDS: s2a._class(), corpus.INDEX: "docs/INDEX.md"}],
        {"steering/capsule.md": "# steering\n\n[a link](../docs/INDEX.md)\n",
         "docs/INDEX.md": "# the index\n\n[one](one.md)\n[two](two.md)\n",
         "docs/one.md": s2a._front(**{corpus.AUTHORITY: s2a._top(), corpus.OWNS: "a-topic"}),
         "docs/two.md": "# two\n"},
    )

    assert _rendered(ctx) == _rendered(ctx), (
        "a page rendered twice produced two different files -- a clock, or an order nobody declared"
    )


# --------------------------------------------------------------------------------------------
# 6. A resolver nobody answers for is refused, never rendered as an empty view.
# --------------------------------------------------------------------------------------------
def test_a_view_resolved_by_a_kind_nothing_answers_for_is_refused_by_name():
    class Declaring:
        id = READER.id
        raw = {resolution.BLOCK: [{resolution.ID: "whatever", resolution.KIND: "nobody-answers",
                                   resolution.PARAMS: {}}]}

    ctx = s2a._host([{corpus.PATH: "docs/", corpus.HOLDS: s2a._class()}], {"docs/a.md": "# a\n"})
    try:
        resolution.resolved_of(ctx, Declaring())
    except resolution.ResolutionError as exc:
        assert "nobody-answers" in str(exc), "the refusal does not name the kind it could not find"
    else:
        raise AssertionError("a view resolved by nothing rendered instead of being refused")


teardown_module = s2a.teardown_module
