"""Acceptance: the norms an agent is held to form one coherent tree (ADR-024).

Held here, on a started host:

  1. the published tree is coherent: `check` reads it and FF-NORMS passes;
  2. a host extends the tree with its own doctrine and rule, deriving from a published cardinal, by
     declaration alone, and stays green;
  3. an orphan, a contradiction and an unenforced MUST in the host's norms are refused, each by its code;
  4. a host stance that narrows a rule without an exception is refused, and one whose exception expired;
  5. a MUST may name an enforcer a taken adapter vouches for -- held while the host declares it, and
     NT-UNENFORCED once the host declares it no more.

Every address, genre and code is read from the declarations and the module that owns them.
"""

from __future__ import annotations

import json
import sys
import unittest

from harness import KIT, REPO, Fixtures

import norms
from manifest import Manifest
from test_adapters import documents_of
from test_pinned_kit import said

CORE = Manifest(KIT)
STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
PUBLISHED = [n for d in TAKEN for doc in documents_of(d, norms.NORMS[0]["validates"]) for n in doc]
GRAMMAR = next(c.documents[d["id"]] for c in CORE.capabilities for d in c.raw.get("documents", [])
               if d["validates"] == norms.GENRES[0]["validates"])
ROOT = next(n for n in PUBLISHED if not n.get("derives_from"))
RULE = next(n for n in PUBLISHED if n.get("modality") == "SHOULD")
DERIVES = [g["id"] for g in GRAMMAR["genres"] if g.get("derives")]
HOST_NORMS = next(i["target"] for c in CORE.capabilities for i in c.installs
                  if i.get("validates") == norms.NORMS[0]["validates"])
HOST_DOCTRINE = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == "doctrine")


def _norm(identity, genre, **fields):
    return {"schema_version": 1, "id": f"host@1.0.0#{identity}", "genre": genre, "title": identity,
            "says": "a fixture norm", "publisher": "the fixture host", **fields}


class Norms(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def write_norms(self, host, rows):
        (host / HOST_NORMS).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n")

    def test_500_the_published_tree_is_coherent_and_a_host_extends_it_by_declaration(self):
        host = self.started()
        doctrine = _norm("our-doctrine", DERIVES[0], derives_from=ROOT["id"])
        rule = _norm("our-rule", DERIVES[1], derives_from=doctrine["id"], modality="SHOULD", subject="our-subject")
        self.write_norms(host, [doctrine, rule])
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, said(checked))
        self.assertIn("normative tree", checked.stdout)

    def test_501_an_orphan_a_contradiction_and_an_unenforced_must_are_refused_by_code(self):
        host = self.started()
        self.write_norms(host, [
            _norm("an-orphan", DERIVES[0]),
            _norm("a-contradiction", DERIVES[1], derives_from=RULE["derives_from"], modality="SHOULD NOT",
                  subject=RULE["subject"]),
            _norm("an-unenforced-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                  subject="nothing-enforces-this")])
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        for code in ("NT-ORPHAN", "NT-CONTRADICTS", "NT-UNENFORCED"):
            self.assertIn(code, checked.stdout)

    def test_502_a_narrowing_needs_an_exception_and_an_exception_expires(self):
        host = self.started()
        doctrine = json.loads((host / HOST_DOCTRINE).read_text(encoding="utf-8"))
        loosening = next(w["id"] for w in GRAMMAR["stance_vocabulary"] if w.get("loosens"))
        row = {"id": RULE["id"], "stance": loosening, "holds": "less, for now", "declared_at": "2026-10-16",
               "declared_by": "the fixture"}
        doctrine["stances"] = [row]
        (host / HOST_DOCTRINE).write_text(json.dumps(doctrine, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.assertIn("NT-LOOSENED", self.run_kit(KIT, host, "check").stdout)
        row["exception"] = {"adr": "ADR-1", "owner": "the owner", "expires": "2000-01-01", "compensating": "a review"}
        (host / HOST_DOCTRINE).write_text(json.dumps(doctrine, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.assertIn("NT-EXPIRED", self.run_kit(KIT, host, "check").stdout)


    def test_503_a_must_may_name_an_enforcer_a_taken_adapter_finds_in_the_host(self):
        vouching = next(doc for d in TAKEN for doc in documents_of(d, norms.VOUCHED["validates"]))
        must = _norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                     subject="held-by-the-build-tool", enforced_by=[f"{vouching['prefix']}:test"])

        def checked(commands):
            host = self.host()
            value = into = {}
            *steps, last = vouching["pointer"].split(".")
            for step in steps:
                into = into.setdefault(step, {})
            into[last] = commands
            (host / vouching["path"]).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
            ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
            self.assertEqual(0, ran.returncode, said(ran))
            self.write_norms(host, [must])
            return self.run_kit(KIT, host, "check")

        held = checked({"test": "run the suite", "build": "build it"})
        self.assertNotIn("NT-UNENFORCED", held.stdout, said(held))
        self.assertEqual(0, held.returncode, said(held))
        unheld = checked({"build": "build it"})
        self.assertNotEqual(0, unheld.returncode)
        self.assertIn(f"NT-UNENFORCED {must['id']}", unheld.stdout)

    def test_504_prove_runs_the_command_a_must_names_and_fails_on_red(self):
        """Found by an audit: a MUST vouched for by a command nothing ran was enforced on paper only.
        `prove` runs every command a MUST names; the git pre-push hook runs it after `check`."""
        vouching = next(doc for d in TAKEN for doc in documents_of(d, norms.VOUCHED["validates"]))
        must = _norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                     subject="held-by-the-build-tool", enforced_by=[f"{vouching['prefix']}:test"])

        def proved(command):
            host = self.host()
            value = into = {}
            *steps, last = vouching["pointer"].split(".")
            for step in steps:
                into = into.setdefault(step, {})
            into[last] = {"test": command}
            (host / vouching["path"]).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
            ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
            self.assertEqual(0, ran.returncode, said(ran))
            self.write_norms(host, [must])
            return self.run_kit(KIT, host, "prove")

        green = proved(f"\"{sys.executable}\" -c \"raise SystemExit(0)\"")
        self.assertEqual(0, green.returncode, said(green))
        self.assertIn("1 enforcer command(s) green", green.stdout)
        red = proved(f"\"{sys.executable}\" -c \"raise SystemExit(3)\"")
        self.assertEqual(1, red.returncode, said(red))
        self.assertIn("RED (exit 3)", red.stdout)

    def test_505_a_must_whose_command_cannot_be_read_is_refused_never_read_as_nothing_to_run(self):
        """Found by a second audit: a vouching declaration missing the command printed 'nothing to run'
        and exited 0 -- the MUST was enforced by nobody, and the push went out."""
        vouching = next(doc for d in TAKEN for doc in documents_of(d, norms.VOUCHED["validates"]))
        must = _norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                     subject="held-by-the-build-tool", enforced_by=[f"{vouching['prefix']}:test"])
        host = self.host()
        value = into = {}
        *steps, last = vouching["pointer"].split(".")
        for step in steps:
            into = into.setdefault(step, {})
        into[last] = {"build": "build it"}
        (host / vouching["path"]).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        self.write_norms(host, [must])
        refused = self.run_kit(KIT, host, "prove")
        self.assertEqual(1, refused.returncode, said(refused))
        self.assertIn("cannot be run", refused.stdout)

if __name__ == "__main__":
    unittest.main()
