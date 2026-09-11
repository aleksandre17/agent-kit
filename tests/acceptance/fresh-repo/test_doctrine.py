"""Acceptance: the doctrine CARRIER -- a bundle that is an ordinary capability, and a zero that
is declared.

The thing under test is not "does a doctrine page render". It is a decision (ADR-004): the kit
ships the CARRIER and the GRAMMAR of conduct doctrine and ships no doctrine at all. Three failure
modes follow from that, and every test here is one of them:

  1. **The supplied default.** A framework that shipped a starter cardinal set would have
     installed an opinion on behalf of a party nobody asked, and a host would never afterwards be
     able to tell its own norm from the vendor's. So the kit's own repository publishes NO bundle,
     and that is asserted against the real manifest rather than trusted.

  2. **The silent zero.** A host that has taken no doctrine must SAY the doctrine in force is
     none, in those words, and `check` must be green on it. A page that simply ended would read
     exactly like a host whose doctrine failed to render.

  3. **The privileged plane.** If doctrine needed a loader, a `when:` engine or a second install
     grammar, every future bundle would cost a code change and the condition would live where no
     host can reach it. So the bundle exercised here is declared in the kit's ORDINARY vocabulary
     -- `requires`, `provides`, `installs`, `composes` -- its environment condition is a `requires`
     on a profile fact, and nothing in any interpreter knows the word `doctrine`.

The bundle is a FIXTURE and is deliberately not shipped: it is added to a copy of the real kit at
test time, which is the same thing a third-party publisher does, and is therefore the proof that
a publisher needs nothing from this repository.

Nothing here restates what the kit declares. Every path, word and address is read from the
declaration that owns it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import FIXTURES, KIT, Fixtures

MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
CARRIER = json.loads((KIT / "capabilities/doctrine/capability.json").read_text(encoding="utf-8"))
GRAMMAR = json.loads((KIT / "capabilities/doctrine/grammar.json").read_text(encoding="utf-8"))

BUNDLE_FIXTURE = FIXTURES / "doctrine-bundle"
BUNDLE = json.loads((BUNDLE_FIXTURE / "capability.json").read_text(encoding="utf-8"))
CARDINALS = json.loads((BUNDLE_FIXTURE / "cardinals.json").read_text(encoding="utf-8"))

#: The schema a published set of doctrine is judged by, by the name its declaration gives it --
#: asked of the capability that declares it, so that renaming it cannot leave this suite agreeing
#: with a memory of the kit.
CARDINAL_SCHEMA = next(name for name in CARRIER["declares"]["schemas"]
                       if name in {item.get("validates") for item in BUNDLE["installs"]})

#: Where a host's answers live, and under which word -- asked of the BUNDLE's own composition,
#: which is the declaration that names the source it reads them from.
STANCE_SOURCE = BUNDLE["composes"]["base"]["sources"][0]
STANCE_LIST = BUNDLE["composes"]["base"]["list"]
ADDRESSED_BY = BUNDLE["composes"]["base"]["named_by"]

SCHEMA_VERSION = 1


def carrier_install(name: str) -> dict:
    found = [item for item in CARRIER["installs"] if item.get("reads_as") == name]
    assert len(found) == 1, f"{name} does not resolve to exactly one install of the carrier"
    return found[0]


PAGE = next(item["target"] for item in CARRIER["installs"] if item["mode"] == "projection")
LAW_PAGE = carrier_install(STANCE_SOURCE)["target"]
ROLL = next(item["target"] for item in BUNDLE["installs"] if item["mode"] == "projection")
PUBLISHED = next(item["target"] for item in BUNDLE["installs"]
                 if item.get("reads_as") == BUNDLE["composes"]["instances"])

#: Where a bundle's payload lives inside a kit, derived from the bundle's own declaration: the
#: same route the kit uses for every other capability, and never a path this suite invented.
PAYLOAD = {item["source"]: BUNDLE_FIXTURE / Path(item["source"]).name
           for item in BUNDLE["installs"] if item.get("source")}


#: Every file the CARRIER is made of, asked of its own declaration: the declaration, the grammar
#: it ships, the payloads it installs and the schemas it declares. A fixture kit is copied from
#: the LOCK, which carries what the lock recorded at the moment it was taken -- so a capability
#: declared since then is not in it. Enumerated here rather than listed, so that a file added to
#: the carrier tomorrow travels with it and nobody has to remember this line exists.
CARRIER_FILES = (
    ["capabilities/doctrine/capability.json"]
    + [document["source"] for document in CARRIER["documents"]]
    + [item["source"] for item in CARRIER["installs"] if item.get("source")]
    + [MANIFEST["schemas"][name] for name in CARRIER["declares"]["schemas"]]
)


def bundle_kit(mutate=None) -> Path:
    """A copy of the REAL kit with a third-party bundle added to it -- declaration, payload and a
    manifest row, and nothing else. Exactly what a publisher outside this repository does."""
    added = [(BUNDLE_FIXTURE / "capability.json", f"capabilities/{BUNDLE['id']}/capability.json")]
    added += [(source, target) for target, source in PAYLOAD.items()]
    added += [(KIT / rel, rel) for rel in CARRIER_FILES]

    def patch(kit: Path) -> None:
        declaration = f"capabilities/{BUNDLE['id']}/capability.json"
        if mutate:
            value = json.loads((kit / declaration).read_text(encoding="utf-8"))
            mutate(value)
            (kit / declaration).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        Fixtures.edit_json(kit, "MANIFEST.json", lambda m: m["capabilities"].append(
            {"id": BUNDLE["id"], "declaration": declaration}))

    return Fixtures.fixture_kit("doctrine", patch=patch, add=[(src, rel) for src, rel in added])


DECLARED_AT = "2026-09-11T00:00:00+00:00"
DECLARED_BY = "the acceptance suite"


def law_page(host: Path) -> dict:
    return json.loads((host / LAW_PAGE).read_text(encoding="utf-8"))


def write_law_page(host: Path, value: dict) -> None:
    (host / LAW_PAGE).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def stance(host: Path, address: str, word: str, holds: str = "as published, whole") -> None:
    """One stance, authored where the carrier declared a host authors one: a row in the host's own
    law page, naming the ADDRESS it answers. Never a line edited into what a publisher shipped --
    there is no field for one there, which is why a fork cannot be taken even by accident."""
    row = {ADDRESSED_BY: address, "stance": word, "holds": holds,
           "declared_at": DECLARED_AT, "declared_by": DECLARED_BY}
    page = law_page(host)
    page[STANCE_LIST].append(row)
    write_law_page(host, page)


class DoctrineCarrier(Fixtures, unittest.TestCase):

    def test_145_a_host_that_declared_no_doctrine_projects_a_page_saying_the_doctrine_in_force_is_none(self):
        """The zero is DECLARED and occupies space on the surface. A host may legitimately take no
        doctrine at all, and the one thing the kit may not do about that is leave the page blank:
        a surface that said nothing would read exactly like a host whose doctrine failed to
        render, and nobody standing at it could tell which they were looking at."""
        host = self.installed()
        page = (host / PAGE).read_text(encoding="utf-8")
        self.assertIn("THE DOCTRINE IN FORCE IS NONE", page,
                      "a host with no doctrine did not say so in the register the decision fixed")
        self.assertIn("No bundle is installed", page)
        self.assertFalse(list((host / Path(PUBLISHED).parent).glob("*")) if (host / Path(PUBLISHED).parent).exists() else [],
                         "the kit put doctrine on a host that asked for none")

    def test_146_check_is_green_on_a_host_that_has_taken_no_doctrine_at_all(self):
        """Declaring no doctrine is a legal, complete state. A gate that failed on it would be the
        kit smuggling in a requirement to accept its opinions -- which is the one thing a carrier
        may never do."""
        host = self.installed()
        read = self.run_kit(KIT, host, "check")
        self.assertEqual(0, read.returncode, "a host with no doctrine was failed by a gate")

    def test_147_the_kit_itself_publishes_no_doctrine_bundle_and_this_is_read_from_its_manifest(self):
        """The claim that the engine holds no norm is worth nothing if it is only written down. No
        capability this kit ships may install a published set of doctrine: the day one does, this
        fails, and the decision is renegotiated rather than eroded."""
        publishers = []
        for entry in MANIFEST["capabilities"]:
            declaration = json.loads((KIT / entry["declaration"]).read_text(encoding="utf-8"))
            if any(item.get("validates") == CARDINAL_SCHEMA for item in declaration["installs"]):
                publishers.append(entry["id"])
        self.assertEqual([], publishers,
                         f"this kit ships doctrine of its own, in {publishers}; the carrier is no "
                         f"longer proven on a host that declared none")

    def test_148_a_doctrine_bundle_installs_as_an_ordinary_capability_with_no_privileged_plane(self):
        """A publisher outside this repository adds a declaration, a payload and a manifest row --
        the same three things every capability is -- and the resolver, the installer and the
        renderer carry it unchanged. Nothing in any interpreter knows the word doctrine."""
        host = self.installed(bundle_kit())
        chosen = json.loads((host / ".agents/project/project.json").read_text(encoding="utf-8"))
        self.assertIn(BUNDLE["id"], chosen["capabilities"], "the bundle was not composed at all")
        self.assertTrue((host / PUBLISHED).exists(), "the bundle's published set did not land")
        self.assertTrue((host / ROLL).exists(), "the bundle projected no roll")
        self.assertEqual(0, self.run_kit(bundle_kit(), host, "check").returncode,
                         "taking doctrine made a gate fail")

    def test_149_every_cardinal_a_bundle_published_is_named_on_the_roll_including_unanswered_ones(self):
        """The named silence. A host that has answered nothing must see every address it has not
        answered, one by one -- because a page showing only the answered ones reads identically to
        a host that had answered everything, and the difference is the whole point of the roll."""
        host = self.installed(bundle_kit())
        roll = (host / ROLL).read_text(encoding="utf-8")
        for cardinal in CARDINALS:
            self.assertIn(cardinal["id"], roll, "a published address was omitted from the roll")
        self.assertEqual(len(CARDINALS), roll.count("UNANSWERED"),
                         "a cardinal this host said nothing about was not named as unanswered")

    def test_150_a_host_amends_by_declaring_a_stance_against_an_address_and_never_by_editing(self):
        """The amendment that cannot fork. The host writes nothing into the vendored set -- it
        could not, the schema has no field for a stance -- and instead declares, in its own plane,
        one word of the declared vocabulary against `bundle@semver#id`. The roll then reads the
        two side by side, and the vendored document is byte-for-byte its publisher's."""
        kit = bundle_kit()
        host = self.installed(kit)
        published_before = (host / PUBLISHED).read_bytes()
        answered, word = CARDINALS[0]["id"], GRAMMAR["stance_vocabulary"][1]["id"]
        stance(host, answered, word, "only where the reader cannot ask a question")
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode, "render refused a stance")

        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn(word, roll, "the stance this host declared never reached the roll")
        self.assertEqual(len(CARDINALS) - 1, roll.count("UNANSWERED"),
                         "answering one address did not change what the roll says about it")
        self.assertEqual(published_before, (host / PUBLISHED).read_bytes(),
                         "the vendored set changed; an amendment became a fork")
        register = (host / PAGE).read_text(encoding="utf-8")
        self.assertIn(answered, register, "the stance register does not cite the address")
        self.assertIn(DECLARED_AT, register,
                      "a stance reached a surface without the date it was taken")

    def test_151_a_stance_answering_an_address_no_bundle_in_force_carries_is_an_orphan_and_is_counted(self):
        """Two hosts on two versions are told apart by CITATION, not by prose -- so an address is
        the identity of a document and a stance outlives the version it answered. A stance whose
        address nothing in force carries is therefore neither an error nor a row to be quietly
        dropped: it is an ORPHAN, counted where the roll is read and still legible in full where
        this host authored it. A withdrawn bundle does not unsay what was said about it."""
        kit = bundle_kit()
        host = self.installed(kit)
        withdrawn = f"{BUNDLE['id']}@0.0.1#a-cardinal-this-bundle-no-longer-publishes"
        stance(host, withdrawn, GRAMMAR["stance_vocabulary"][0]["id"])
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode,
                         "a stance citing a withdrawn address was treated as a failure")

        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn("address no document in force carries", roll,
                      "an orphaned stance was dropped from the roll instead of being counted")
        self.assertNotIn(withdrawn, roll,
                         "the roll named an address no document in force carries, as though it "
                         "were a document -- a citation that resolves to nothing must not render "
                         "as one that resolved")
        self.assertIn(withdrawn, (host / PAGE).read_text(encoding="utf-8"),
                      "an orphaned stance vanished from the one page that is this host's own")

    def test_152_the_vocabulary_an_answer_is_spoken_in_is_declared_and_a_host_may_add_a_word_to_it(self):
        """Comparability, and openness, in one property. An answer in private words is legible to
        nobody but its author, so the words are DECLARED -- and because they are declared in a
        document rather than in an interpreter, a host that needs one this kit never thought of
        adds a ROW. A new stance is never a code change, and the kit ships the words without ever
        shipping a verdict spoken in them."""
        kit = bundle_kit()
        host = self.installed(kit)
        page = (host / PAGE).read_text(encoding="utf-8")
        for word in GRAMMAR["stance_vocabulary"]:
            self.assertIn(word["id"], page, "a declared stance word reaches no surface")

        invented = "holds-it-under-protest"
        law = law_page(host)
        law["stance_vocabulary"].append({"id": invented, "means": "a word this kit never shipped"})
        write_law_page(host, law)
        stance(host, CARDINALS[1]["id"], invented)
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode,
                         "a host's own stance word was refused by machinery it does not own")
        self.assertIn(invented, (host / ROLL).read_text(encoding="utf-8"),
                      "a host-declared stance word did not reach the roll")
        self.assertIn(invented, (host / PAGE).read_text(encoding="utf-8"),
                      "a host-declared stance word is not legible beside the ones the kit ships")

    def test_153_an_environment_chapter_is_a_requires_on_a_profile_fact_and_nothing_else(self):
        """The `when:` engine that was refused. A bundle that applies only in some environments
        states the condition in its DECLARATION, using the mechanism every other capability uses;
        where the fact is not measured, the bundle is unavailable with a reason, its documents are
        not installed, and `check` is still green -- an absent chapter is a state, not a failure."""
        def demand_the_unmeasurable(declaration):
            declaration["requires"] = [
                need if need["kind"] != "fact" else {**need, "id": "a.fact.nothing.detects"}
                for need in declaration["requires"]
            ]

        kit = bundle_kit(mutate=demand_the_unmeasurable)
        host = self.installed(kit)
        chosen = json.loads((host / ".agents/project/project.json").read_text(encoding="utf-8"))
        self.assertNotIn(BUNDLE["id"], chosen["capabilities"],
                         "a bundle whose environment was never measured was installed anyway")
        self.assertIn(BUNDLE["id"], [row["id"] for row in chosen.get("unavailable", [])],
                      "an unavailable bundle was dropped silently instead of being named")
        self.assertFalse((host / PUBLISHED).exists(),
                         "a chapter that does not apply here published its documents anyway")
        self.assertEqual(0, self.run_kit(kit, host, "check").returncode,
                         "an environment that does not hold was treated as a failure")

    def test_154_the_host_law_page_is_seeded_once_and_no_later_run_reads_it_for_writing(self):
        """The host's own authorship. What a host records about the doctrine it has taken is
        BINDING -- written once if absent and never again -- because an upgrade that could rewrite
        it would be the publisher editing the host's answer. The page it feeds then stops saying
        the doctrine in force is none, which is the other half: the zero must be able to end."""
        kit = bundle_kit()
        host = self.installed(kit)
        law = law_page(host)
        law["bundles"].append({
            "id": BUNDLE["id"], "version": BUNDLE["version"],
            "taken_at": DECLARED_AT, "taken_by": DECLARED_BY,
            "because": "so that the carrier is exercised by a host that took something",
        })
        (host / LAW_PAGE).write_text(json.dumps(law, indent=2) + "\n", encoding="utf-8")

        self.assertEqual(0, self.run_kit(kit, host, "init", "--approve", "again").returncode,
                         "a second init refused an approved host")
        kept = law_page(host)
        self.assertEqual(law["bundles"], kept["bundles"],
                         "an install overwrote what the host had declared for itself")
        page = (host / PAGE).read_text(encoding="utf-8")
        self.assertNotIn("THE DOCTRINE IN FORCE IS NONE", page,
                         "a host holding doctrine was still told it holds none")
        self.assertIn(BUNDLE["version"], page, "the version in force is not legible from the page")


if __name__ == "__main__":
    unittest.main()
