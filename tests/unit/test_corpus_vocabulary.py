"""Unit: the corpus vocabularies and the SHAPE of a corpus map (ADR-019, decisions 1-3, slices S0/S1).

What is being proved here is that a host can state what its corpus is made of in tens of rows, and
that the two ways of getting that statement wrong are decidable from the DECLARATIONS ALONE -- no
gate module exists yet, and none is needed to know the answer. That is the point of the slice: S1
ships a contract a machine can decide; S2 ships the machine.

Five properties:

  1. the shipped vocabularies validate against the schema that declares them, and every kind names
     a plane that exists -- a kind with no plane is a document that appears in no section of any
     catalog, which is how a corpus acquires a part nobody reads;
  2. the authority vocabulary is COMPARABLE and its top state is unreachable from a place -- stated
     without naming a state, because the property is structural: the one state a place may not
     declare is the most binding one, and the default ceiling binds less;
  3. a corpus-map row conferring a class the vocabulary does not declare is REFUSED -- and the
     fixture that is refused is SCHEMA-VALID first, so the refusal is the vocabulary's and not the
     shape's;
  4. a row reaching for an authority ceiling the vocabulary does not permit a place to declare is
     REFUSED, by the same two-layer reading;
  5. a host that declares NO corpus map at all is legal and green. Lazy materialization: the
     mechanism ships on day one, the artifact is instantiated the day it has content.

No word of any of the three vocabularies appears in this file. Every value under test is read from
the declaration that owns it -- a test that spelled out a class name would be the second home the
ADR exists to prevent, and it would still pass after the row it named was deleted.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import validation  # noqa: E402

GOVERNANCE = KIT / "capabilities" / "governance" / "capability.json"
CORPUS_MAP_SCHEMA = "corpus-map"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str) -> dict:
    """A schema by the name the MANIFEST registers it under -- never by a path spelled here."""
    manifest = _json(KIT / "MANIFEST.json")
    assert name in manifest["schemas"], f"{name}: not registered in kit/MANIFEST.json"
    return _json(KIT / manifest["schemas"][name])


def _document(document_id: str) -> tuple[dict, str]:
    """A governance document and the schema it declares itself validated by."""
    rows = [d for d in _json(GOVERNANCE)["documents"] if d["id"] == document_id]
    assert len(rows) == 1, f"{document_id}: not declared exactly once by the governance capability"
    return _json(KIT / rows[0]["source"]), rows[0]["validates"]


def _vocabulary() -> dict:
    return _document("record_keeping")[0]


# --------------------------------------------------------------------------------------------
# The resolution S1 makes DECIDABLE and S2 will run as a gate. It holds no word of the
# vocabulary: which classes exist, and which authorities a place may name, are read from the
# vocabulary rows themselves. The field names it does hold (`holds`, `authority_ceiling`) belong
# to the corpus-map schema, which is the document being read -- not to the vocabulary being
# resolved against.
# --------------------------------------------------------------------------------------------
def _refusals(places: list[dict], vocabulary: dict) -> list[tuple[int, str]]:
    classes = {row["id"] for row in vocabulary["kinds"]}
    ceilings = {row["id"] for row in vocabulary["authorities"] if row["place_default"]}
    out: list[tuple[int, str]] = []
    for index, place in enumerate(places):
        if place["holds"] not in classes:
            out.append((index, "holds"))
        ceiling = place.get("authority_ceiling")
        if ceiling is not None and ceiling not in ceilings:
            out.append((index, "authority_ceiling"))
    return out


def _map_of(places: list[dict]) -> dict:
    """A map file. It carries an `id` because a host may write SEVERAL of them and they are read
    as one collection -- where a file with no identity is a file that cannot be told from another
    (S2a; the field was added when the map was declared readable)."""
    return {"schema_version": 1, "id": "fixture", "summary": "fixture, for this test only",
            "places": places}


def _declared_class(vocabulary: dict) -> str:
    return vocabulary["kinds"][0]["id"]


def _declared_ceiling(vocabulary: dict) -> str:
    return next(a["id"] for a in vocabulary["authorities"] if a["place_default"])


def _forbidden_ceiling(vocabulary: dict) -> str:
    return next(a["id"] for a in vocabulary["authorities"] if not a["place_default"])


# --------------------------------------------------------------------------------------------
# 1. The vocabularies
# --------------------------------------------------------------------------------------------
def test_the_shipped_vocabularies_validate_against_the_schemas_that_declare_them(capsys):
    for document_id in ("record_keeping", "obligation_markers"):
        document, schema_name = _document(document_id)
        errors = validation.validate(document, _schema(schema_name))
        print(f"{document_id} -> {schema_name}: {len(errors)} error(s)")
        assert errors == [], f"{document_id}: {errors}"


def test_every_class_names_a_plane_that_exists_and_every_plane_is_reachable(capsys):
    vocabulary = _vocabulary()
    planes = [p["id"] for p in vocabulary["planes"]]
    assert len(planes) == len(set(planes)), "a plane id is declared twice"

    census: dict[str, int] = {plane: 0 for plane in planes}
    for kind in vocabulary["kinds"]:
        assert kind["plane"] in census, (
            f"kind {kind['id']!r} names plane {kind['plane']!r}, which no row declares"
        )
        census[kind["plane"]] += 1

    print(f"{len(vocabulary['kinds'])} class(es) over {len(planes)} plane(s):")
    for plane, count in census.items():
        print(f"  {plane:12} {count}")

    empty = [plane for plane, count in census.items() if count == 0]
    assert not empty, f"plane(s) no class belongs to -- a catalog section that can never fill: {empty}"


def test_the_authority_vocabulary_is_comparable_and_its_top_is_unreachable_from_a_place(capsys):
    authorities = _vocabulary()["authorities"]
    ids = [a["id"] for a in authorities]
    assert len(ids) == len(set(ids)), "an authority id is declared twice"

    top = max(a["binding_rank"] for a in authorities)
    defaults = [a["id"] for a in authorities if a["place_default"]]
    print(f"{len(authorities)} authority state(s); top rank {top}; default ceiling {defaults}")

    assert len(defaults) == 1, (
        "the vocabulary declares no single default ceiling, or more than one -- and a place that "
        "names none would then be capped by whichever row a reader happened to take first"
    )
    default = next(a for a in authorities if a["place_default"])
    assert default["binding_rank"] < top, (
        "the DEFAULT ceiling is the most binding state there is -- then a place that says nothing "
        "at all admits the strongest claim in the vocabulary, and silence has granted authority. "
        "A place may lower a claim and may never raise one (ADR-019 amendment 1), which is only "
        "worth anything if the unstated cap is below the top."
    )
    assert len([a for a in authorities if a["binding_rank"] == top]) == 1, (
        "two states tie at the most binding rank, so which one a claim must OWN against is "
        "decided by whichever row a reader reached first"
    )

    defaults = [a for a in authorities if a["place_default"]]
    assert len(defaults) == 1, f"the default ceiling is declared {len(defaults)} times, not once"
    assert defaults[0]["place_default"], "the default ceiling is a state no place may declare"
    assert defaults[0]["binding_rank"] < top, (
        "the DEFAULT ceiling is the top authority -- every unmapped place would confer the highest "
        "authority in the system by saying nothing"
    )


def test_every_obligation_marker_is_calibrated_in_both_directions(capsys):
    markers = _document("obligation_markers")[0]["markers"]
    for marker in markers:
        pattern = re.compile(marker["pattern"])
        print(f"  {marker['id']:20} proves={marker['proves']!r}")
        assert pattern.search(marker["proves"]), (
            f"{marker['id']}: the line it must match does not match -- a detector that detects "
            f"nothing reports that nothing is owed"
        )
        assert not pattern.search(marker["admits"]), (
            f"{marker['id']}: the lookalike it must tolerate is matched -- a false obligation "
            f"routes work that does not exist"
        )
    print(f"{len(markers)} marker(s), calibrated both ways")


# --------------------------------------------------------------------------------------------
# 2. The corpus map
# --------------------------------------------------------------------------------------------
def test_a_well_formed_corpus_map_is_accepted_by_shape_and_by_vocabulary():
    vocabulary = _vocabulary()
    good = _map_of([
        {
            "path": "docs/decisions/",
            "holds": _declared_class(vocabulary),
            "authority_ceiling": _declared_ceiling(vocabulary),
            "entry": True,
            "read_when": ["is this already decided"],
            "indexed_by": "docs/decisions/README.md",
        },
        {"path": "docs/guides/", "holds": _declared_class(vocabulary)},
    ])
    assert validation.validate(good, _schema(CORPUS_MAP_SCHEMA)) == []
    assert _refusals(good["places"], vocabulary) == []


def test_a_place_conferring_a_class_the_vocabulary_does_not_declare_is_refused():
    vocabulary = _vocabulary()
    fixture = _map_of([{"path": "docs/somewhere/", "holds": "a-class-nobody-declares"}])

    # The SHAPE admits it: a class is a string, and a schema that enumerated the classes would be
    # the vocabulary's second home.
    assert validation.validate(fixture, _schema(CORPUS_MAP_SCHEMA)) == []
    # The VOCABULARY refuses it.
    assert _refusals(fixture["places"], vocabulary) == [(0, "holds")]


def test_a_place_reaching_above_the_ceiling_a_place_default_is_refused():
    vocabulary = _vocabulary()
    reaching = _map_of([{
        "path": "docs/somewhere/",
        "holds": _declared_class(vocabulary),
        "authority_ceiling": _forbidden_ceiling(vocabulary),
    }])
    invented = _map_of([{
        "path": "docs/somewhere/",
        "holds": _declared_class(vocabulary),
        "authority_ceiling": "an-authority-nobody-declares",
    }])

    for fixture in (reaching, invented):
        assert validation.validate(fixture, _schema(CORPUS_MAP_SCHEMA)) == []
        assert _refusals(fixture["places"], vocabulary) == [(0, "authority_ceiling")]


def test_the_shape_refuses_a_row_that_says_nothing_and_a_field_nobody_declared():
    schema = _schema(CORPUS_MAP_SCHEMA)
    assert validation.validate(_map_of([{"path": "docs/somewhere/"}]), schema), (
        "a place row with no class is accepted -- a row that confers nothing is a comment"
    )
    assert validation.validate(
        _map_of([{"path": "docs/x/", "holds": _declared_class(_vocabulary()), "plane": "invented"}]),
        schema,
    ), "a field the schema does not declare is accepted -- a plane on a place would be a second home"
    assert validation.validate({"schema_version": 1, "places": []}, schema), (
        "an empty map is accepted -- the absence of a map is the absence of a map, not a row saying nothing"
    )


def test_a_host_that_declares_no_corpus_map_is_legal_and_green(capsys):
    """Lazy materialization (ADR-019 decision 4, and the kit's own stance on a cast nobody made).

    Nothing in the kit requires a host to have a corpus map: no floor row demands the place, no
    install writes one, and the resolution over a host that declares none refuses nothing. The
    corpus map is instantiated the day it has content and not before.
    """
    vocabulary = _vocabulary()
    assert _refusals([], vocabulary) == [], "a host with no places declared is refused something"

    manifest = _json(KIT / "MANIFEST.json")
    declarations = [_json(KIT / entry["declaration"]) for entry in manifest["capabilities"]]

    shipped = [d for c in declarations for d in c.get("documents", [])
               if d["validates"] == CORPUS_MAP_SCHEMA]
    assert shipped == [], f"the kit ships a corpus map of its own: {shipped}"

    carriers = [i for c in declarations for i in c.get("installs", [])
                if i.get("validates") == CORPUS_MAP_SCHEMA]
    assert [i["mode"] for i in carriers] == ["space"], (
        f"the corpus map arrives by something other than a SPACE a host may write in: {carriers}. "
        f"A seed would put a map in every host on the day it installed, and a map nobody authored "
        f"is a statement about a corpus nobody read"
    )
    assert all("source" not in i for i in carriers), (
        f"a corpus-map install carries content: {carriers}"
    )

    layout = _json(KIT / "capabilities" / "governance" / "host-layout.json")
    demanded = [e for e in layout["entries"] if "corpus" in e["path"] and "pending" not in e]
    assert demanded == [], f"the host floor demands a corpus place: {demanded}"
    print("no floor row, no install and no shipped instance requires a corpus map")
