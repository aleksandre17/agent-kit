"""Acceptance: a skill is declared once and served to every product that reads skills (ADR-024).

A skill is the Agent Skills unit: its name and description are declared in one row, its body is prose,
its scripts travel beside it. Each published bundle and each host may declare skills; every surface
whose adapter renders the `skills` view serves each one at its product's home. Held here:

  1. a started host serves every skill its starter takes, at every served surface's skill home, with
     the front matter read from the declaration and every supporting file beside it, and `check` green;
  2. a skill the HOST declares -- a fixture nobody published -- is served by `render` alone, and one
     whose file leaves its own skill directory is refused by its code, with nothing written;
  3. a name outside the Agent Skills rule is refused by the contract.

Every home, id and code is read from the adapters, the bundles and the module that owns it.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

import serving
import skills as skills_resolver
from manifest import Manifest
from skills import SkillError
from test_adapters import ADAPTERS, documents_of, surfaces_of
from test_pinned_kit import said

CORE = Manifest(KIT)
#: The served view a product's skill home renders: the one whose members the skills resolver produces.
VIEW = next(v["id"] for c in CORE.capabilities for i in c.installs if i.get("shape") == serving.SHAPE
            for v in i["serves"]["views"] if (v.get("members_from") or {}).get("kind") == skills_resolver.CONTRACT)
#: Where the host declares its own skills, and the directory their files are relative to.
HOST_SKILLS = next(i["target"] for c in CORE.capabilities for i in c.installs
                   if i.get("validates") == skills_resolver.CONTRACT)
HOST_BASE = HOST_SKILLS.rsplit("/", 1)[0]
STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
HOMES = sorted({(r["target"], r["suffix"]) for a in ADAPTERS if a.resolve() in TAKEN
                for s in surfaces_of(a) for r in s["renders"] if r["view"] == VIEW})
PUBLISHED = [skill for d in TAKEN for document in documents_of(d, skills_resolver.CONTRACT)
             for skill in document[skills_resolver.LIST]]


class Skills(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def declare(self, host, skills, files):
        for rel, text in files.items():
            (host / HOST_BASE / rel).parent.mkdir(parents=True, exist_ok=True)
            (host / HOST_BASE / rel).write_text(text, encoding="utf-8", newline="\n")
        (host / HOST_SKILLS).write_text(json.dumps({"schema_version": 1, skills_resolver.LIST: skills},
                                                   indent=2) + "\n",
                                        encoding="utf-8", newline="\n")

    def test_420_every_taken_skill_reaches_every_skill_home_with_its_declared_front_matter(self):
        self.assertTrue(HOMES, "the standard starter serves at least one product that reads skills")
        self.assertTrue(PUBLISHED, "the standard starter takes at least one published skill")
        host = self.started()
        for home, suffix in HOMES:
            for skill in PUBLISHED:
                with self.subTest(home=home, skill=skill["id"]):
                    text = (host / f"{home.rstrip('/')}/{skill['id']}{suffix}").read_text(encoding="utf-8")
                    self.assertTrue(text.startswith(f"---\nname: {skill['id']}\n"))
                    self.assertIn(f"description: {json.dumps(skill['description'], ensure_ascii=False)}\n", text)
                    for rel in skill.get("files", []):
                        beside = rel[len(rel.rsplit("/", 2)[0]) + 1:] if rel.count("/") >= 2 else rel
                        self.assertTrue((host / home / skill["id"] / beside).is_file(), beside)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_421_a_skill_the_host_declares_is_served_and_one_that_leaves_its_directory_is_refused(self):
        host = self.started()
        body = {"skills/fixture-skill/body.md": "Run the fixture.\n",
                "skills/fixture-skill/scripts/run.py": "print('fixture')\n"}
        self.declare(host, [{"id": "fixture-skill", "description": "A fixture no bundle published.",
                             "body": "skills/fixture-skill/body.md",
                             "files": ["skills/fixture-skill/scripts/run.py"]}], body)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        for home, suffix in HOMES:
            self.assertIn("Run the fixture.", (host / f"{home}fixture-skill{suffix}").read_text(encoding="utf-8"))
            self.assertTrue((host / f"{home}fixture-skill/scripts/run.py").is_file())
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

        self.declare(host, [{"id": "fixture-skill", "description": "A fixture no bundle published.",
                             "body": "skills/fixture-skill/body.md", "files": ["skills/elsewhere.md"]}],
                     {"skills/elsewhere.md": "outside\n"})
        refused = self.run_kit(KIT, host, "render")
        self.assertIn(f"[{SkillError.code}]", said(refused))
        self.assertFalse(any((host / f"{home}fixture-skill/elsewhere.md").exists() for home, _ in HOMES))

    def test_423_a_host_extends_a_published_skill_with_its_own_chapter_and_stance(self):
        """A host's stack and selections reach the ONE served skill by declaration: the publisher's
        chapters stay, the host's chapter is served beside them and indexed, its stance is its own."""
        base = next(s for s in PUBLISHED if s.get("chapters"))
        host = self.started()
        self.declare(host, [], {"skills/stack/our-stack.md": "# Our stack\nA fixture chapter.\n"})
        statement = json.loads((host / HOST_SKILLS).read_text(encoding="utf-8"))
        statement[skills_resolver.EXTENDS] = [{"skill": base["id"], "stances": ["A fixture stance of this host."],
                                               "chapters": [{"id": "our-stack", "title": "Our stack",
                                                             "summary": "the fixture's own chapter",
                                                             "file": "skills/stack/our-stack.md"}]}]
        (host / HOST_SKILLS).write_text(json.dumps(statement, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        for home, suffix in HOMES:
            served = (host / f"{home}{base['id']}{suffix}").read_text(encoding="utf-8")
            self.assertIn("Our stack", served)
            self.assertIn("A fixture stance of this host.", served)
            self.assertTrue(all(c["title"] in served for c in base["chapters"]))
            self.assertIn("A fixture chapter.", (host / f"{home}{base['id']}/{skills_resolver.REFERENCES}our-stack.md")
                          .read_text(encoding="utf-8"))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_422_a_name_outside_the_agent_skills_rule_is_refused_by_the_contract(self):
        host = self.started()
        self.declare(host, [{"id": "Not--A-Name", "description": "x", "body": "skills/x/body.md"}],
                     {"skills/x/body.md": "x\n"})
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn("Not--A-Name", said(checked))


if __name__ == "__main__":
    unittest.main()
