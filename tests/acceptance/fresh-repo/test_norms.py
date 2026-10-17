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

    def test_506_a_push_is_proved_by_what_it_touches_and_never_twice_on_the_same_bytes(self):
        """The owner: a one-line change must not run every suite (ADR-025 amendment 4, Cardinal IX)."""
        import subprocess
        from harness import install_target

        vouching = next(doc for d in TAKEN for doc in documents_of(d, norms.VOUCHED["validates"]))
        prefix = vouching["prefix"]
        ran = self._temp("ran-")

        def counting(name):
            return f'python -c "open(r\'{(ran / name).as_posix()}\', \'a\').write(\'x\')"'

        host = self.host()
        value = into = {}
        *steps, last = vouching["pointer"].split(".")
        for step in steps:
            into = into.setdefault(step, {})
        into[last] = {"test": counting("all"), "test-web": counting("web")}
        (host / vouching["path"]).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        started = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, started.returncode, said(started))
        self.write_norms(host, [_norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                                      subject="held-by-the-build-tool", enforced_by=[f"{prefix}:test"])])
        areas = host / install_target("delivery", reads_as="areas")
        body = json.loads(areas.read_text(encoding="utf-8"))
        body["areas"] = [{"id": "web", "paths": "^web/", "undo": "reversible", "because": "a fixture",
                          "proved_by": [f"{prefix}:test-web"]},
                         {"id": "docs", "paths": "^docs/", "undo": "reversible", "because": "a fixture", "proved_by": []}]
        body["default_proved_by"] = []
        areas.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")

        def count(name):
            return len((ran / name).read_text()) if (ran / name).exists() else 0

        (host / "web").mkdir()
        (host / "web" / "app.ts").write_text("export const a = 1;\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "one line in the web app")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertEqual((1, 0), (count("web"), count("all")), "a web change runs the web tests, not every suite")
        self.assertIn(f"proved by {prefix}:test-web", proved.stdout)

        again = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, again.returncode, said(again))
        self.assertEqual(1, count("web"), "a green proof is not run twice on the same bytes")
        self.assertIn("already went green on these exact bytes", again.stdout)

        git("push", "-q")
        (host / "docs").mkdir(exist_ok=True)
        (host / "docs" / "guide.md").write_text("# a guide\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "prose")
        prose = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, prose.returncode, said(prose))
        self.assertIn("nothing beyond `check` proves this change", prose.stdout)
        self.assertEqual((1, 0), (count("web"), count("all")))

        full = self.run_kit(KIT, host, "prove", "--full")
        self.assertEqual(0, full.returncode, said(full))
        self.assertEqual(1, count("all"), "--full runs every command a MUST names")
        self.assertEqual(2, count("web"), "everything runs every area's own proof too, which no MUST names (N2)")

    def test_507_a_host_with_no_build_kit_proves_an_area_by_the_command_its_policy_declares(self):
        """Any host -- the kit itself among them -- declares its own proof commands in its delivery
        policy (`host:<key>`), and an area's `proved_by` runs with no MUST naming it."""
        import subprocess
        from harness import install_target

        ran = self._temp("ran-")
        host = self.started()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        body["commands"] = {"lib": f'python -c "open(r\'{(ran / "lib").as_posix()}\', \'a\').write(\'x\')"'}
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        areas = host / install_target("delivery", reads_as="areas")
        shape = json.loads(areas.read_text(encoding="utf-8"))
        shape["areas"] = [{"id": "lib", "paths": "^lib/", "undo": "reversible", "because": "a fixture",
                           "proved_by": ["host:lib"]}]
        areas.write_text(json.dumps(shape, indent=2) + "\n", encoding="utf-8", newline="\n")

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")
        (host / "lib").mkdir()
        (host / "lib" / "a.py").write_text("A = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "a library change")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertIn("proved by host:lib", proved.stdout)
        self.assertTrue((ran / "lib").exists(), "the host's own declared command ran")

    def _pushed_host(self, manifest: dict):
        """A started host with a build-tool manifest, committed and pushed -- so what follows is what a push
        carries."""
        import subprocess

        host = self.started()
        (host / "stack-kit.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")
        return host, git

    def _counting(self, ran, name):
        return f'python -c "open(r\'{(ran / name).as_posix()}\', \'a\').write(\'x\')"'

    def test_508_a_new_host_drafts_its_areas_from_its_modules_and_a_change_is_proved_by_its_own(self):
        """Found by the foreign-project experiment: a new host's areas were empty, so a one-line UI change
        and the deploy manifest weighed alike and were proved by nothing."""
        ran = self._temp("ran-")
        host, git = self._pushed_host({"modules": {"web": {"type": "node-vite", "path": "web"},
                                                   "api": {"type": "java-boot", "path": "."}},
                                       "commands": {"test": self._counting(ran, "all"),
                                                    "test-web": self._counting(ran, "web"),
                                                    "test-api": self._counting(ran, "api")}})
        draft = self.run_kit(KIT, host, "areas")
        self.assertEqual(0, draft.returncode, said(draft))
        self.assertIn("module-web", draft.stdout)
        self.assertIn("door", draft.stdout)
        approved = self.run_kit(KIT, host, "areas", "--approve", "acceptance-suite")
        self.assertEqual(0, approved.returncode, said(approved))
        git("add", "-A")
        git("commit", "-qm", "the drafted areas")
        git("push", "-q")
        (host / "web").mkdir(exist_ok=True)
        (host / "web" / "main.tsx").write_text("export const a = 1;\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "one line in the web app")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertTrue((ran / "web").exists() and not (ran / "all").exists() and not (ran / "api").exists(),
                        "a web change is proved by the web module's tests alone")
        ui = self.run_kit(KIT, host, "weigh", "--path", "web/main.tsx")
        deploy = self.run_kit(KIT, host, "weigh", "--path", "stack-kit.json")
        self.assertNotEqual(ui.stdout.split("\n")[1:2], deploy.stdout.split("\n")[1:2],
                            "a UI line and the deploy manifest weigh differently")

    def test_509_with_no_area_and_no_must_a_push_is_proved_by_the_test_command_the_host_declares(self):
        ran = self._temp("ran-")
        host, git = self._pushed_host({"modules": {}, "commands": {"test": self._counting(ran, "all")}})
        (host / "src.txt").write_text("a change\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "a change")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertIn("proved by the test command this host declares", proved.stdout)
        self.assertTrue((ran / "all").exists(), "the host's declared test command ran")

    def test_510_a_push_is_proved_as_published_by_the_refs_it_carries_and_a_record_must_match(self):
        """Found by review: a push could switch off or rewrite its own proof, a push of another ref proved
        nothing, a MUST was said to hold where its enforcer never ran, and a cache record was honoured
        because it existed."""
        import subprocess
        from harness import install_target

        ran = self._temp("ran-")
        host = self.started()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        body["commands"] = {"lib": self._counting(ran, "lib"), "all": self._counting(ran, "all")}
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        areas = host / install_target("delivery", reads_as="areas")
        shape = json.loads(areas.read_text(encoding="utf-8"))
        shape["areas"] = [{"id": "lib", "paths": "^lib/", "undo": "reversible", "because": "a fixture",
                           "proved_by": ["host:lib"]}]
        shape["default_proved_by"] = []
        areas.write_text(json.dumps(shape, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.write_norms(host, [_norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                                      subject="held-by-the-whole-suite", enforced_by=["host:all"])])

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)
            return done.stdout.strip()

        def count(name):
            return len((ran / name).read_text()) if (ran / name).exists() else 0

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")
        hook = (host / ".githooks" / "pre-push").read_text(encoding="utf-8")
        self.assertIn("read -r", hook, "the hook reads the refs git pushes")
        self.assertIn('--pushed "$pushed"', hook)

        brief = self.run_kit(KIT, host, "check", "--brief")
        lines = brief.stdout.splitlines()
        for i, line in enumerate(lines):
            if "READ the normative tree" in line:
                self.assertIn("FF-NORMS", lines[i - 1], "a gate's own lines appear only with its header")

        (host / "lib").mkdir()
        (host / "lib" / "a.py").write_text("A = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "a library change")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertEqual((1, 0), (count("lib"), count("all")))
        self.assertIn("host:all not run", proved.stdout, "a MUST holds only where its own enforcer ran")
        self.assertNotIn("it holds host@1.0.0#our-must", proved.stdout)

        records = [p for p in host.rglob("*.json") if p.parent.name == "proofs"]
        self.assertEqual(1, len(records), "the green proof is recorded")
        forged = json.loads(records[0].read_text(encoding="utf-8"))
        forged["kit_version"] = "0.0.0"
        records[0].write_text(json.dumps(forged), encoding="utf-8")
        again = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, again.returncode, said(again))
        self.assertEqual(2, count("lib"), "a record whose content does not match is not honoured")

        git("push", "-q")
        shape["areas"][0]["proved_by"] = []
        areas.write_text(json.dumps(shape, indent=2) + "\n", encoding="utf-8", newline="\n")
        body["commands"]["lib"] = "exit 0"
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        (host / "lib" / "b.py").write_text("B = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "a change that switches off its own proof")
        loosening = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, loosening.returncode, said(loosening))
        self.assertIn("loosens its own proof", loosening.stdout)
        self.assertEqual(3, count("lib"), "the proof runs as the published side declares it")

        git("push", "-q")
        published = git("rev-parse", "HEAD")
        git("checkout", "-q", "-b", "other")
        (host / "lib" / "c.py").write_text("C = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "on another branch")
        other = git("rev-parse", "HEAD")
        git("checkout", "-q", "-")
        pushed = self.run_kit(KIT, host, "prove", "--pushed", f"{other}:{published}", "--full")
        self.assertEqual(1, pushed.returncode, said(pushed))
        self.assertIn("is not HEAD", pushed.stdout)
        self.assertIn("prove judges the working tree: push from a clean checkout of what you push", pushed.stdout)
        self.assertEqual(0, count("all"), "a pushed ref that is not HEAD is refused, never proved on other bytes")
        (host / "lib" / "stray.py").write_text("S = 1\n", encoding="utf-8")
        dirty = self.run_kit(KIT, host, "prove", "--pushed", f"{published}:{published}", "--full")
        self.assertEqual(1, dirty.returncode, said(dirty))
        self.assertIn("the working tree is not clean", dirty.stdout)
        self.assertEqual(0, count("all"), "--full does not bypass the guard")

    def test_512_a_push_cannot_weigh_itself_lighter_by_editing_the_class_rows_N5(self):
        import subprocess
        from harness import install_target
        from test_pinned_kit import PINNED

        ran = self._temp("ran-")
        host = self.started()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        body["commands"] = {"lib": self._counting(ran, "lib"), "all": self._counting(ran, "all")}
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        areas = host / install_target("delivery", reads_as="areas")
        shape = json.loads(areas.read_text(encoding="utf-8"))
        shape["areas"] = [{"id": "lib", "paths": "^lib/", "undo": "irreversible", "because": "a fixture",
                           "proved_by": ["host:lib"]}]
        shape["default_proved_by"] = []
        areas.write_text(json.dumps(shape, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.write_norms(host, [_norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                                      subject="held-by-the-whole-suite", enforced_by=["host:all"])])

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")
        kit = host / PINNED
        catalogue = kit / "capabilities" / "delivery" / "work-classes.json"
        rows = json.loads(catalogue.read_text(encoding="utf-8"))
        heavy = next(r for r in rows["classes"] if r.get("admits", {}).get("undo") == "irreversible")
        heavy["requires"] = [r for r in heavy["requires"] if r != "decision"]
        catalogue.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8", newline="\n")
        (host / "lib").mkdir()
        (host / "lib" / "a.py").write_text("A = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "an irreversible change that rewrites the class it weighs")
        proved = self.run_kit(kit, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertTrue((ran / "all").exists(), "weighed by the catalogue as published, it owes a decision: "
                                                "proved by everything -- " + said(proved))

    def test_513_a_root_module_waits_for_the_kit_planes_and_a_drafted_area_follows_its_draft_M3(self):
        import re
        import subprocess
        from harness import install_target

        host = self.host()
        (host / "stack-kit.json").write_text(json.dumps({"modules": {"api": {"type": "java-boot", "path": "."}},
                                                         "commands": {"test": "exit 0"}}, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
        started = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, started.returncode, said(started))
        areas = host / install_target("delivery", reads_as="areas")
        ids = [a["id"] for a in json.loads(areas.read_text(encoding="utf-8"))["areas"]]
        self.assertNotIn("module-api", ids, "a root module drafted before the planes would claim them")
        waits = self.run_kit(KIT, host, "areas")
        self.assertIn("waits for the kit planes", waits.stdout)

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        git("add", "-A")
        git("commit", "-qm", "the install")
        approved = self.run_kit(KIT, host, "areas", "--approve", "acceptance-suite")
        self.assertEqual(0, approved.returncode, said(approved))
        doc = json.loads(areas.read_text(encoding="utf-8"))
        root = next(a for a in doc["areas"] if a["id"] == "module-api")
        claims = re.compile(root["paths"])
        self.assertTrue(claims.search("src/App.java"))
        for plane in (".agents/project/x.json", ".githooks/pre-push"):
            self.assertFalse(claims.search(plane), f"the root module claims {plane}")

        stale = "^(?!(?:.*?(?:^docs/))).+"
        doc["areas"] = [dict(a, paths=stale, drafted_as=stale) if a["id"] == "module-api" else a for a in doc["areas"]]
        areas.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
        git("add", "-A")
        git("commit", "-qm", "a root area the verb drafted before the planes")
        redrafted = self.run_kit(KIT, host, "areas", "--approve", "acceptance-suite")
        self.assertEqual(0, redrafted.returncode, said(redrafted))
        doc = json.loads(areas.read_text(encoding="utf-8"))
        self.assertEqual(root["paths"], next(a for a in doc["areas"] if a["id"] == "module-api")["paths"],
                         "an area the verb drafted, unedited, follows the draft")

        doc["areas"] = [dict(a, paths="^src/") if a["id"] == "module-api" else a for a in doc["areas"]]
        areas.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
        kept = self.run_kit(KIT, host, "areas", "--approve", "acceptance-suite")
        self.assertEqual(0, kept.returncode, said(kept))
        self.assertEqual("^src/", next(a for a in json.loads(areas.read_text(encoding="utf-8"))["areas"]
                                       if a["id"] == "module-api")["paths"], "an area the host edited is never touched")
    def test_511_a_push_cannot_drop_the_enforcer_of_a_must_it_is_proved_by(self):
        """Found by review: the MUSTs were read from the tree being pushed, so a push could unname the
        command that proves it."""
        import subprocess
        from harness import install_target

        ran = self._temp("ran-")
        host = self.started()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        body["commands"] = {"all": self._counting(ran, "all")}
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        must = _norm("our-must", DERIVES[1], derives_from=RULE["derives_from"], modality="MUST",
                     subject="held-by-the-whole-suite", enforced_by=["host:all"])
        self.write_norms(host, [must])

        def git(*argv):
            done = subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite",
                                   "-c", "core.hooksPath=/dev/null", *argv], capture_output=True, text=True)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)

        remote = self._temp("remote-")
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git("add", "-A")
        git("commit", "-qm", "the host")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "HEAD")
        self.write_norms(host, [{k: v for k, v in must.items() if k != "enforced_by"} | {"modality": "SHOULD"}])
        (host / "lib").mkdir()
        (host / "lib" / "a.py").write_text("A = 1\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "a change that unnames its own enforcer")
        proved = self.run_kit(KIT, host, "prove")
        self.assertEqual(0, proved.returncode, said(proved))
        self.assertTrue((ran / "all").exists(), "the MUST as published names host:all, and it ran: " + said(proved))


if __name__ == "__main__":
    unittest.main()
