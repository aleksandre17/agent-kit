"""Acceptance: a host extends the kit at declared points, scaffolded on demand (ADR-024).

Held here, on a started host:

  1. the registry lists every point in the shared shape; a member scaffolded at a point carries its
     pending answers, and `check` names each one; the served result composes what the host wrote
     (a standards chapter reaches the served skill);
  2. a newer template merges three ways into a member the host edited; a conflicting one is reported
     and the host's file kept;
  3. a file at a point's place that no member name accounts for is reported.

Every point, path and marker is read from the registry the kit derives from its own declarations.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

import extensions
import skills as skills_resolver
import validation
from context import Context
from manifest import Manifest
from test_pinned_kit import said

CORE = Manifest(KIT)
STARTER = REPO / "starters" / "standard.json"


class Extensions(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def registry(self, host):
        return extensions.registry(Context(kit_root=KIT, host_root=host))

    def chapter_point(self, host):
        """A point whose members merge into a served skill, read from what it says it merges into."""
        return next(p for p in self.registry(host) if p["cardinality"] == "many" and "skill" in p["merges_into"]
                    and p["host_path"].endswith("{name}.md"))

    def test_510_a_point_is_scaffolded_with_its_pending_answers_and_composed_into_what_is_served(self):
        host = self.started()
        listed = self.run_kit(KIT, host, "extend", "--list", "--json")
        self.assertEqual(0, listed.returncode, said(listed))
        document = json.loads(listed.stdout[listed.stdout.index("{"):])
        self.assertEqual([], validation.validate(document, CORE.schema("extension-points")))
        point = self.chapter_point(host)
        self.assertEqual(0, self.run_kit(KIT, host, "extend", "--point", point["id"], "--name", "platform",
                                         "--approve", "acceptance-suite").returncode)
        rel = point["host_path"].replace("{name}", "platform")
        text = (host / rel).read_text(encoding="utf-8")
        self.assertTrue(extensions.pending(text))
        checked = self.run_kit(KIT, host, "check")
        self.assertIn(f"PENDING  {rel}", checked.stdout)
        again = self.run_kit(KIT, host, "extend", "--point", point["id"], "--name", "platform", "--approve", "acceptance-suite")
        self.assertIn("never overwritten", again.stdout)
        # Composed: the host points its skills declaration at the chapter, and the served skill carries it.
        declaration = next(p for p in self.registry(host) if p["schema"] == skills_resolver.CONTRACT)["host_path"]
        statement = json.loads((host / declaration).read_text(encoding="utf-8"))
        published = json.loads((REPO / "bundles" / "engineering-standards" / "skills.json").read_text(encoding="utf-8"))
        statement[skills_resolver.EXTENDS] = [{"skill": published["skills"][0]["id"], "chapters": [
            {"id": "platform", "title": "Our platform", "summary": "the host's chapter", "path": rel}]}]
        (host / declaration).write_text(json.dumps(statement, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        served = list(host.glob(f"**/{published['skills'][0]['id']}/{skills_resolver.REFERENCES}platform.md"))
        self.assertTrue(served, "the host's chapter reached no served skill")

    def test_511_a_newer_template_merges_into_an_edited_member_and_a_conflict_keeps_the_host_file(self):
        host = self.started()
        point = self.chapter_point(host)
        self.run_kit(KIT, host, "extend", "--point", point["id"], "--name", "merge", "--approve", "acceptance-suite")
        rel = point["host_path"].replace("{name}", "merge")
        ledger_rel = next(i["target"] for c in CORE.capabilities for i in c.installs
                          if i.get("validates") == extensions.LEDGER_CONTRACT)
        ledger = json.loads((host / ledger_rel).read_text(encoding="utf-8"))
        current = ledger["generated"][0]["base"]
        # The member was written from an OLDER template: one more line at its end.
        ledger["generated"][0]["base"] = current + "An older closing line.\n"
        (host / ledger_rel).write_text(json.dumps(ledger) + "\n", encoding="utf-8")
        (host / rel).write_text("The host's own first line.\n" + current + "An older closing line.\n", encoding="utf-8")
        merged = self.run_kit(KIT, host, "extend", "--merge", "--approve", "acceptance-suite")
        self.assertEqual(0, merged.returncode, said(merged))
        text = (host / rel).read_text(encoding="utf-8")
        self.assertIn("The host's own first line.", text)
        self.assertNotIn("An older closing line.", text)
        # A conflict: the host rewrote the very line the template changes.
        ledger = json.loads((host / ledger_rel).read_text(encoding="utf-8"))
        ledger["generated"][0]["base"] = current.replace("this host's chapter", "an older chapter title")
        (host / ledger_rel).write_text(json.dumps(ledger) + "\n", encoding="utf-8")
        mine = current.replace("this host's chapter", "the host's own title")
        (host / rel).write_text(mine, encoding="utf-8")
        conflicted = self.run_kit(KIT, host, "extend", "--merge", "--approve", "acceptance-suite")
        self.assertEqual(1, conflicted.returncode, said(conflicted))
        self.assertIn("CONFLICT", conflicted.stdout)
        self.assertEqual(mine, (host / rel).read_text(encoding="utf-8"))

    def test_512_a_file_no_member_name_accounts_for_is_reported(self):
        host = self.started()
        point = self.chapter_point(host)
        stray = host / point["root"] / "Not A Member.txt"
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_text("stray\n", encoding="utf-8")
        self.assertIn("REPORTED", self.run_kit(KIT, host, "check").stdout)


if __name__ == "__main__":
    unittest.main()
