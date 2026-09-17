"""Acceptance: roles -- a definition that is COMPOSED, and the second body that cannot be written.

The thing under test is not "does a role render". It is a failure mode: **two files that are both
right.** One role with two homes -- a body in the framework and a body in the host -- each
internally correct, drifting apart, and invisible from either side because there is nothing at
either one to contradict. By the time anyone notices, both have been obeyed by different people
for months.

So these tests are mostly about what CANNOT happen:

  1. a host with no roles says so, and projects nothing -- the zero occupies space;
  2. a definition carries the archetype's body although no host file contains it;
  3. the binding protocol is declared ONCE and reaches every definition -- proved by changing the
     one declaration and watching every definition move together, which is the only evidence that
     rules out a copy;
  4. an overlay that tries to restate the archetype's body is REFUSED at the boundary, by the
     schema, rather than by anybody's discipline;
  5. an overlay naming a base nobody declares renders UNBOUND and fails a gate -- it is neither
     skipped nor a traceback, because an overlay alone reads exactly like a complete role;
  6. a role with no shipped ancestor is the SAME grammar, not an exception to it -- and an
     archetype declared by both the kit and the host is refused, being the same two-home defect
     one level up;
  7. archetypes nobody took up are counted and NOT named on a host surface, because a framework
     that prints its cast has organised the host before meeting it;
  8. the plane is rebuilt wholesale, so a role that is withdrawn leaves nothing behind.

Nothing here restates what the kit declares. Every path, name and word is read from the
declaration that owns it: a test carrying its own copy of the default set stops measuring the kit
and starts agreeing with a snapshot of it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest  # noqa: E402
import space  # noqa: E402 -- the kit's one home for a declared empty space; harness sets the path

CAPABILITY = json.loads((KIT / "capabilities/roles/capability.json").read_text(encoding="utf-8"))
ARCHETYPES = json.loads((KIT / "roles/archetypes.json").read_text(encoding="utf-8"))
OVERLAY_SCHEMA = json.loads((KIT / "schemas/overlay.schema.json").read_text(encoding="utf-8"))

#: The words the CONTRACTS give both sides, read from the capability's own block and from the
#: schemas -- never spelled here as though this suite had invented them.
SPEC = CAPABILITY["composes"]
BASE_FIELD = SPEC["base"]["named_by"]
BASE_LIST = SPEC["base"]["list"]
SHARED_LIST = SPEC["shared"]["list"]
GATE = CAPABILITY["gates"][0]["id"]

SCHEMA_VERSION = 1


def install_named(name: str) -> dict:
    """One of this capability's install statements, by the name it declared for itself. The path
    is asked of the declaration that owns it and never written down twice."""
    found = [item for item in CAPABILITY["installs"]
             if item.get("reads_as") == name or item["target"].endswith(name)]
    assert len(found) == 1, f"{name} does not resolve to exactly one install: {found}"
    return found[0]


OVERLAYS = install_named("role_overlays")["target"]
HOST_ARCHETYPES = install_named("host_archetypes")["target"]
ROLL = install_named("ROLES.md")["target"]
DEFINITIONS = [item for item in CAPABILITY["installs"] if item.get("each")][0]
PLANE = DEFINITIONS["target"]
SUFFIX = DEFINITIONS["each"].get("suffix", "")


def a_shipped_archetype() -> dict:
    """One archetype the kit declares, read from the registry. Which one is not the point and is
    never named here: naming it would put a second home for the kit's roster in this file."""
    return ARCHETYPES[BASE_LIST][0]


class Roles(Fixtures, unittest.TestCase):

    # -- authoring, as a host does it -------------------------------------------------------
    def overlay(self, host: Path, **fields) -> Path:
        record = {"schema_version": SCHEMA_VERSION, **fields}
        path = host / OVERLAYS / f"{record['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return path

    def host_registry(self, host: Path, archetypes=(), protocol=()) -> None:
        (host / HOST_ARCHETYPES).write_text(json.dumps({
            "schema_version": SCHEMA_VERSION,
            SHARED_LIST: list(protocol),
            BASE_LIST: list(archetypes),
        }, indent=2) + "\n", encoding="utf-8")

    def definition(self, host: Path, role: str) -> str:
        return (host / PLANE.rstrip("/") / f"{role}{SUFFIX}").read_text(encoding="utf-8")

    def rendered(self, host: Path):
        result = self.run_kit(KIT, host, "render")
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    # -- 1. the zero ------------------------------------------------------------------------
    def test_90_a_host_that_has_hired_nobody_says_so_and_the_empty_plane_still_survives_a_clone(self):
        """The declared zero, told twice and never fabricated: the roll states the absence in
        words -- a page that simply ended would read exactly like a page whose roles failed to
        render -- and the plane holds no ROLE PAGE.

        It does hold the one marker that makes its emptiness survive a repository. This test used
        to assert the plane held NOTHING, "the same fact told by the filesystem", and that was
        true of a filesystem and never of a clone: git carries files, so the directory itself
        disappeared on the next checkout and the floor then reported a DRAWN path as MISSING. The
        stronger claim is asserted here -- no page, and the space still exists (`space`)."""
        host = self.installed()
        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn("declared no role", roll)
        plane = host / PLANE.rstrip("/")
        self.assertTrue(plane.is_dir(), f"{PLANE} is drawn, so it exists even holding nobody")
        self.assertEqual([space.marker(Manifest(KIT))], sorted(p.name for p in plane.glob("*")))

        # ... and the zero is not bought with a red gate: an honest absence is a PASSING state.
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, checked.stdout)
        self.assertIn(f"PASS  {GATE}", checked.stdout)

    # -- 2. the body arrives from somewhere no host file holds -------------------------------
    def test_91_a_definition_carries_a_body_that_exists_in_no_file_the_host_authored(self):
        """The composition, and the proof that it IS one: the archetype's seam reaches the
        definition, and appears in nothing the host wrote. A host that had to hold the body in
        order to render it would be the two-home state with extra steps."""
        host = self.installed()
        base = a_shipped_archetype()
        self.overlay(host, id="a-role-this-host-hired", **{BASE_FIELD: base["id"]})
        self.rendered(host)

        body = self.definition(host, "a-role-this-host-hired")
        self.assertIn(base["seam"], body)
        for duty in base["duty"]:
            self.assertIn(duty, body)
        for exemplar in base["reference_class"]:
            self.assertIn(exemplar, body)

        # the whole binding plane -- everything this host authored or was seeded -- holds no
        # sentence of that body anywhere.
        authored = [path for path in (host / ".agents/project").rglob("*") if path.is_file()]
        self.assertTrue(authored, "the binding plane is empty; this assertion would be vacuous")
        for path in authored:
            self.assertNotIn(base["seam"], path.read_text(encoding="utf-8"),
                             f"{path.name} holds a second home for the archetype's body")

    # -- 3. one declaration, every definition ------------------------------------------------
    def test_92_the_binding_protocol_is_declared_once_and_moves_every_definition_together(self):
        """The cure, measured. Every definition carries every protocol line -- and when the ONE
        declaration changes, every definition changes with it.

        Presence alone would not prove anything: a copy in each definition looks identical from
        here. Only the MOVE distinguishes a projection from a duplicate, which is why this test
        edits one file in a fixture kit and reads the effect in two definitions at once.
        """
        host = self.installed()
        base = a_shipped_archetype()
        for role in ("one-role", "another-role"):
            self.overlay(host, id=role, **{BASE_FIELD: base["id"]})
        self.rendered(host)

        for role in ("one-role", "another-role"):
            body = self.definition(host, role)
            for line in ARCHETYPES[SHARED_LIST]:
                self.assertIn(line["says"], body, f"{role} is missing a binding line")

        moved = "a line added to the ONE declaration, which every definition must now carry"

        def amend_the_one_declaration(kit: Path):
            self.edit_json(kit, "roles/archetypes.json", lambda document:
                           document[SHARED_LIST].append({"id": "an-amended-line", "says": moved}))

        amended = self.fixture_kit("protocol-amended", amend_the_one_declaration)
        result = self.run_kit(amended, host, "render")
        self.assertEqual(0, result.returncode, result.stderr)
        for role in ("one-role", "another-role"):
            self.assertIn(moved, self.definition(host, role),
                          f"{role} did not follow the declaration it is supposed to project")

    # -- 4. the second body cannot be written ------------------------------------------------
    def test_93_an_overlay_that_restates_the_archetypes_body_is_refused_at_the_boundary(self):
        """The structural half. A host does not merely *should not* write a second body -- the
        overlay schema declares none of the archetype's vocabulary and refuses what it did not
        declare, so the divergence is a state that cannot be expressed.

        Asserted twice: against the schema, so the closure is provably the reason; and against a
        real run, so it is provably enforced rather than merely written down.
        """
        declared = set(OVERLAY_SCHEMA["properties"])
        forbidden = set(a_shipped_archetype()) - {"id"}
        self.assertFalse(declared & forbidden,
                         "the overlay schema shares vocabulary with the archetype it overlays")
        self.assertFalse(OVERLAY_SCHEMA["additionalProperties"],
                         "an overlay open to undeclared properties can hold a second body")

        host = self.installed()
        base = a_shipped_archetype()
        smuggled = sorted(forbidden)[0]
        self.overlay(host, id="a-role-with-opinions", **{BASE_FIELD: base["id"],
                                                        smuggled: base[smuggled]})
        result = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(smuggled, result.stderr)

    # -- 5. an overlay whose base is gone ----------------------------------------------------
    def test_94_an_overlay_naming_a_base_nobody_declares_renders_unbound_and_fails_a_gate(self):
        """Two readings of one fact, taken independently. The SURFACE says UNBOUND in words,
        because an overlay alone reads exactly like a complete role to anyone who opens the file;
        the GATE says it with an exit code. Neither is allowed to be the only one that knows, and
        the definition is neither omitted nor a traceback."""
        host = self.installed()
        self.overlay(host, id="a-role-whose-base-was-renamed",
                     **{BASE_FIELD: "an-archetype-nobody-declares"})
        self.rendered(host)

        body = self.definition(host, "a-role-whose-base-was-renamed")
        self.assertIn("UNBOUND", body)
        self.assertIn("an-archetype-nobody-declares", body)

        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(1, checked.returncode)
        self.assertIn(f"FAIL  {GATE}", checked.stdout)
        self.assertIn("a-role-whose-base-was-renamed", checked.stdout)

        # ... and the sensor's other edge: a role whose base IS declared is not flagged, so the
        # gate has a measured edge rather than a habit of naming everything.
        self.overlay(host, id="a-role-whose-base-is-there",
                     **{BASE_FIELD: a_shipped_archetype()["id"]})
        self.rendered(host)
        again = self.run_kit(KIT, host, "check")
        self.assertNotIn("a-role-whose-base-is-there", again.stdout)

    # -- 6. a role with no shipped ancestor --------------------------------------------------
    def test_95_a_host_origin_role_is_the_same_grammar_and_not_an_exception(self):
        """A role the discipline has never heard of is not a special case: the host declares an
        archetype of its own, in the same shape, and an overlay names it. Two sources for bases,
        one grammar -- and the composition cannot tell which source a base came from, which is
        the point.

        The second half is the same two-home defect one level up: an id declared by BOTH the kit
        and the host is refused, not ordered, because whichever lost would go on reading as true.
        """
        host = self.installed()
        mine = {
            "id": "a-specialism-only-this-repository-has",
            "seam": "the one part of this repository nobody else has to understand",
            "duty": ["the local invariant, before the general one"],
            "reference_class": ["whatever this repository has already proved works"],
        }
        self.host_registry(host, archetypes=[mine])
        self.overlay(host, id="the-local-specialist", **{BASE_FIELD: mine["id"]})
        self.rendered(host)

        body = self.definition(host, "the-local-specialist")
        self.assertIn(mine["seam"], body)
        self.assertNotIn("UNBOUND", body)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

        # the same id, declared twice -- once by the kit, once by the host.
        self.host_registry(host, archetypes=[dict(a_shipped_archetype())])
        clash = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, clash.returncode)
        self.assertNotIn("Traceback", clash.stderr)
        self.assertIn(a_shipped_archetype()["id"], clash.stderr)
        self.assertIn("two homes for one judgement", clash.stderr)

    # -- 7. the census counts what it may not name -------------------------------------------
    def test_96_untaken_archetypes_are_counted_and_never_named_on_a_host_surface(self):
        """The line T3 draws, held on purpose rather than by accident. Which roles exist follows
        from what the work IS, so a framework that printed its cast into a host that has chosen
        none of it would have organised that host before meeting it. The count is the honest
        middle: a zero that occupies space, pointing at the declarations where the names live.

        And the other side, so this is not merely a gag: once a host TAKES UP an archetype, the
        name appears -- because at that point the host is the one who named it.
        """
        host = self.installed()
        roll = (host / ROLL).read_text(encoding="utf-8")
        shipped = ARCHETYPES[BASE_LIST]
        self.assertIn(f"{len(shipped)} declared archetype", roll)
        for base in shipped:
            self.assertNotIn(base["id"], roll,
                             "the roll printed a cast into a host that had chosen none of it")

        taken = a_shipped_archetype()
        self.overlay(host, id="a-role-this-host-chose", **{BASE_FIELD: taken["id"]})
        self.rendered(host)
        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn(taken["id"], roll, "an archetype the host took up is host truth and named")
        self.assertIn(f"{len(shipped) - 1} declared archetype", roll)

    # -- 8. the plane has no history ---------------------------------------------------------
    def test_97_a_role_that_is_withdrawn_leaves_nothing_behind(self):
        """A projection has no history: the plane is rebuilt wholesale, so there is nothing for a
        withdrawn role to drift FROM. A definition that outlived its overlay would be the most
        persuasive lie this capability could tell -- a complete-looking role nobody declares."""
        host = self.installed()
        base = a_shipped_archetype()
        for role in ("a-role-that-stays", "a-role-that-goes"):
            self.overlay(host, id=role, **{BASE_FIELD: base["id"]})
        self.rendered(host)
        self.assertTrue((host / PLANE.rstrip("/") / f"a-role-that-goes{SUFFIX}").is_file())

        (host / OVERLAYS / "a-role-that-goes.json").unlink()
        self.rendered(host)
        self.assertFalse((host / PLANE.rstrip("/") / f"a-role-that-goes{SUFFIX}").exists(),
                         "a definition outlived the overlay that declared it")
        self.assertTrue((host / PLANE.rstrip("/") / f"a-role-that-stays{SUFFIX}").is_file())
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
