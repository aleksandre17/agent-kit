"""ADR-012 -- carrying out a succession: the map at its residence, a door that accepts the roster
BY ITS DIGEST, a whole refusal while anything is undecided or anything moved, every removal a
rename aside, a killed act reconciled and finished, and the estate accounting for every path.

Every host is a scratch repository with the FIXTURE prior system copied in. The real second host
is never touched from a test. Every word, place and code is derived from a declaration or from
the module that owns it; a test holding its own copy would pass after the kit changed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

from harness import CLI, FIXTURES, KIT, Fixtures, host_digest

import ephemeral  # noqa: E402 -- the interpreter's path is set by the harness
import estate as estate_module  # noqa: E402
import succession_act as acts  # noqa: E402
import takeover  # noqa: E402
from ports.manifest import Manifest  # noqa: E402
from test_succession import VOCABULARY  # noqa: E402 -- the one derivation of the vocabulary

PRIOR = FIXTURES / "prior-system"
TREE = PRIOR / "tree"
MAP = PRIOR / "map.json"
APPROVER = "acceptance-suite"
RESIDENCE = VOCABULARY["residence"]
EFFECT = {d["id"]: d["effect"] for d in VOCABULARY["dispositions"]}
MANIFEST = Manifest(KIT)
OBSERVED = next(p["root"].rstrip("/") for p in MANIFEST.planes if p["class"] == ephemeral.OBSERVED)
JOURNAL = f"{OBSERVED}/{takeover.JOURNAL}"
#: Record spaces every run writes into (receipts, judgements) -- whatever a run leaves there says
#: a run happened, not that the act wrote. Everything else in the observed plane IS compared.
RECORD_SPACES = [i["target"] for c in MANIFEST.capabilities for i in c.installs
                 if i["target"].endswith("/") and i["target"].startswith(OBSERVED + "/")]
ACT_CODE, MOVED_CODE = acts.ActRefused.code, acts.RosterMoved.code


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_of(host: Path) -> dict:
    return {rel: d for rel, d in host_digest(host).items()
            if not any(rel.startswith(space) for space in RECORD_SPACES)}


def roster_digest(stdout: str) -> str:
    found = re.search(r"^  roster  ([0-9a-f]{64})$", stdout, re.M)
    assert found, f"no roster digest was printed:\n{stdout}"
    return found.group(1)


def code_of(stderr: str):
    found = re.search(r"^kit: \[(\w+)\] ", stderr, re.M)
    return found.group(1) if found else None


def read_journal(host: Path):
    try:
        return json.loads((host / JOURNAL).read_text(encoding="utf-8"))
    except (FileNotFoundError, PermissionError, json.JSONDecodeError):
        return None  # not yet written, held open by Windows, or torn by the kill


class TakeoverTest(Fixtures, unittest.TestCase):

    # -- the fixture ---------------------------------------------------------------------------
    def space(self, host: Path) -> str:
        """A space this host RECEIVED whose mode the vocabulary says may receive a path."""
        recorded = json.loads((host / estate_module.target(self._ctx(host))).read_text("utf-8"))
        spaces = sorted(r["path"] for r in recorded["files"]
                        if r["mode"] in VOCABULARY["receives"] and r["path"].endswith("/")
                        and not RESIDENCE.startswith(r["path"]))
        self.assertTrue(spaces, "this host received no space that may receive a path")
        return spaces[0]

    def _ctx(self, host: Path):
        from context import Context
        return Context(kit_root=KIT, host_root=host)

    def prepared(self, edit=None):
        """An installed host holding the fixture prior system, with a map at its RESIDENCE that
        answers every path: the fixture map, its destinations moved into a receiving space, and
        the one unanswered fixture path answered the way another row of it already is."""
        host = self.installed()
        shutil.copytree(TREE, host, dirs_exist_ok=True)
        space = self.space(host)
        document = json.loads(MAP.read_text(encoding="utf-8"))
        for row in document["rows"]:
            if "to" in row:
                row["to"] = f"{space}legacy/{row['path'].rsplit('/', 1)[-1]}"
        answered = [r["path"] for r in document["rows"]]
        removing = next(r for r in document["rows"] if not EFFECT_RELOCATES[r["disposition"]]
                        and set(r) == {"path", "disposition", "because"})
        for rel in sorted(p.relative_to(TREE).as_posix() for p in TREE.rglob("*") if p.is_file()):
            if not any(rel == a or rel.startswith(a + "/") for a in answered):
                document["rows"].append(dict(removing, path=rel))
        if edit:
            edit(document, space)
        self.place_map(host, document)
        return host, document

    def place_map(self, host: Path, document: dict) -> None:
        (host / RESIDENCE).parent.mkdir(parents=True, exist_ok=True)
        (host / RESIDENCE).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def plan(self, host: Path, *flags) -> str:
        result = self.run_kit(KIT, host, "takeover", "--plan", *flags)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout

    def carry(self, host: Path, digest: str, *flags):
        return self.run_kit(KIT, host, "takeover", "--approve", APPROVER, "--roster", digest, *flags)

    def act_of(self, host: Path) -> dict:
        recorded = json.loads((host / estate_module.target(self._ctx(host))).read_text("utf-8"))
        return recorded[estate_module.SUCCESSION]

    # -- 1. the plan is the act, and writes nothing ----------------------------------------------
    def test_244_a_plan_prints_the_roster_and_its_digest_and_writes_nothing(self):
        host, _ = self.prepared()
        before = tree_of(host)
        stdout = self.plan(host)
        self.assertEqual(before, tree_of(host), "a --plan wrote into the host")
        self.assertRegex(stdout, r"(?m)^  roster  [0-9a-f]{64}$")
        self.assertEqual(roster_digest(stdout), roster_digest(self.plan(host)),
                         "two readings of an unchanged host gave two rosters")

    def test_245_no_act_without_a_door_that_names_the_roster_digest(self):
        host, _ = self.prepared()
        digest = roster_digest(self.plan(host))
        before = tree_of(host)
        for flags in ((), ("--approve", APPROVER)):
            result = self.run_kit(KIT, host, "takeover", *flags)
            self.assertEqual(3, result.returncode, "the act ran without a door naming its roster")
            self.assertIn(digest, result.stderr)
            self.assertEqual(before, tree_of(host))

    # -- 2. the act ---------------------------------------------------------------------------
    def test_246_every_path_goes_exactly_where_the_signed_roster_said_with_its_bytes(self):
        host, _ = self.prepared()
        originals = {p.relative_to(TREE).as_posix(): sha(p) for p in TREE.rglob("*") if p.is_file()}
        self.assertTrue(originals)
        digest = roster_digest(self.plan(host))
        result = self.carry(host, digest)
        self.assertEqual(0, result.returncode, result.stderr)
        [act] = self.act_of(host)
        by_path = {item["path"]: item for item in act["roster"]["paths"]}
        self.assertEqual(sorted(originals), sorted(by_path), "the act did not carry the whole census")
        for rel, original in originals.items():
            item = by_path[rel]
            self.assertFalse((host / rel).exists(), f"{rel} is still in the prior tree")
            self.assertEqual(original, sha(host / item["to"]), f"{rel} did not arrive whole")
            if not EFFECT_RELOCATES[item["disposition"]]:
                self.assertTrue(item["to"].startswith(OBSERVED + "/"),
                                f"{rel} was removed somewhere other than aside: {item['to']}")
        emptied = {item["row"] for item in act["roster"]["paths"] if item["row"] != item["path"]}
        self.assertTrue(emptied)
        for row in emptied:
            self.assertFalse((host / row).exists(), f"{row} was emptied and left standing")

    def test_247_the_estate_accounts_for_every_path_the_act_moved_or_removed(self):
        host, _ = self.prepared()
        planned = self.plan(host)
        digest = roster_digest(planned)
        self.assertEqual(0, self.carry(host, digest).returncode)
        [act] = self.act_of(host)
        self.assertEqual(digest, act["digest"])
        self.assertEqual(APPROVER, act["signed_by"])
        self.assertTrue(act.get("carried_at"), "the account states no moment")
        paths = act["roster"]["paths"]
        self.assertTrue(paths)
        removed = [p for p in paths if not EFFECT_RELOCATES[p["disposition"]]]
        self.assertTrue(removed, "the fixture removed nothing, so nothing here was measured")
        for item in paths:
            self.assertIn(f"  {item['disposition']}  {item['path']}  -> {item['to']}", planned)
            self.assertEqual(item["digest"], sha(host / item["to"]))
        record = json.loads((host / acts.record_path(self._ctx(host), digest)).read_text("utf-8"))
        self.assertEqual(act, record, "the act record and the estate's account disagree")

    # -- 3. whole refusals --------------------------------------------------------------------
    def assertRefusedWhole(self, host: Path, flags, code: str, *named):
        before = tree_of(host)
        result = self.run_kit(KIT, host, "takeover", *flags)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(code, code_of(result.stderr), result.stderr)
        for name in named:
            self.assertIn(name, result.stderr)
        self.assertEqual(before, tree_of(host), "a refused act moved something")

    def test_248_one_undecided_path_of_the_prior_boundary_refuses_the_whole_act(self):
        host, document = self.prepared()
        dropped = document["rows"].pop()
        self.place_map(host, document)
        self.assertRefusedWhole(host, ("--plan",), ACT_CODE, dropped["path"],
                                VOCABULARY["undecided"]["id"])

    def test_249_the_tree_changed_after_the_reading_that_was_signed_refuses_the_act(self):
        host, document = self.prepared()
        digest = roster_digest(self.plan(host))
        victim = next(p for p in sorted(TREE.rglob("*")) if p.is_file()).relative_to(TREE)
        (host / victim).write_text("edited after the roster was signed\n", encoding="utf-8")
        self.assertRefusedWhole(host, ("--approve", APPROVER, "--roster", digest), MOVED_CODE, digest)

    def test_250_the_map_changed_after_the_reading_that_was_signed_refuses_the_act(self):
        def relocate_everything(document, space):
            # Nothing set aside: an aside place is named after the map, so it would carry a map
            # change into the roster by itself and hide whether the map is bound directly.
            mover = next(r for r in document["rows"] if "to" in r)
            document["rows"] = [r if "to" in r else dict(mover, path=r["path"], to=f"{space}legacy-{i}")
                                for i, r in enumerate(document["rows"])]
        host, document = self.prepared(relocate_everything)
        digest = roster_digest(self.plan(host))
        self.place_map(host, dict(document, declared_at=document["declared_at"] + " (amended)"))
        self.assertRefusedWhole(host, ("--approve", APPROVER, "--roster", digest), MOVED_CODE, digest)

    def test_251_a_map_given_from_anywhere_or_absent_from_its_residence_is_refused(self):
        host, _ = self.prepared()
        self.assertRefusedWhole(host, ("--plan", "--map", str(MAP)), ACT_CODE, "residence")
        (host / RESIDENCE).unlink()
        self.assertRefusedWhole(host, ("--plan",), ACT_CODE, RESIDENCE)

    def test_252_a_destination_that_exists_or_that_nothing_accounts_for_refuses_the_act(self):
        host, document = self.prepared()
        mover = next(r for r in document["rows"] if "to" in r)
        source = next(p for p in sorted((TREE / mover["path"]).rglob("*")) if p.is_file())
        target = host / (mover["to"] + "/" + source.relative_to(TREE / mover["path"]).as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the host already has this\n", encoding="utf-8")
        self.assertRefusedWhole(host, ("--plan",), ACT_CODE, "already exists")
        target.unlink()
        mover["to"] = f"{MANIFEST.planes[0]['root'].rstrip('/')}/nothing-accounts-for-this"
        self.place_map(host, document)
        self.assertRefusedWhole(host, ("--plan",), ACT_CODE, "no space that may receive")

    def test_253_a_row_that_would_move_a_path_the_kit_installed_refuses_the_act(self):
        host, document = self.prepared()
        recorded = json.loads((host / estate_module.target(self._ctx(host))).read_text("utf-8"))
        kit_file = next(r["path"] for r in recorded["files"] if r["digest"])
        removing = next(r for r in document["rows"] if not EFFECT_RELOCATES[r["disposition"]])
        document["rows"].append(dict(removing, path=kit_file))
        self.place_map(host, document)
        self.assertRefusedWhole(host, ("--plan",), ACT_CODE, kit_file, "this kit installed it")

    # -- 4. the residence ---------------------------------------------------------------------
    def test_254_the_map_resides_at_a_declared_target_and_inherit_reads_it_there(self):
        host, _ = self.prepared()
        declared = [i for c in MANIFEST.capabilities for i in c.installs if i["target"] == RESIDENCE]
        self.assertEqual(1, len(declared), "the residence is not exactly one declared install target")
        result = self.run_kit(KIT, host, "inherit")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"{(host / RESIDENCE).resolve().as_posix()} -- declared by", result.stdout)

    def test_255_a_vocabulary_whose_effect_the_interpreter_cannot_carry_out_is_refused(self):
        def unknown_effect(kit: Path):
            home = next(d["source"] for c in json.loads((kit / "MANIFEST.json").read_text("utf-8"))["capabilities"]
                        for d in json.loads((kit / c["declaration"]).read_text("utf-8")).get("documents", [])
                        if d["validates"] == "succession")
            self.edit_json(kit, home, lambda doc: doc["dispositions"][-1].update(effect="vanish"))
        kit = self.fixture_kit("unknown-effect", unknown_effect)
        host = self.host()
        result = self.run_kit(kit, host, "inherit")
        self.assertEqual(acts.succession.SuccessionRefused.code, code_of(result.stderr), result.stderr)
        self.assertIn("vanish", result.stderr)

    # -- 5. the uncommitted, and the killed ---------------------------------------------------
    def test_256_uncommitted_bytes_are_carried_as_signed_because_the_digest_not_the_index_binds(self):
        host, _ = self.prepared()
        git = ["git", "-C", str(host), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
        subprocess.run([*git, "commit", "-qm", "fixture"], check=True, capture_output=True)
        victim = next(p for p in sorted(TREE.rglob("*")) if p.is_file()).relative_to(TREE).as_posix()
        (host / victim).write_text("uncommitted work the owner has not saved anywhere else\n",
                                   encoding="utf-8")
        dirty = sha(host / victim)
        digest = roster_digest(self.plan(host))
        self.assertEqual(0, self.carry(host, digest).returncode)
        [act] = self.act_of(host)
        [item] = [p for p in act["roster"]["paths"] if p["path"] == victim]
        self.assertEqual(dirty, item["digest"])
        self.assertEqual(dirty, sha(host / item["to"]), "the uncommitted bytes were not kept whole")

    def test_257_a_killed_act_is_named_by_the_next_run_and_finished_exactly_as_signed(self):
        host, document = self.prepared()
        mover = next(r for r in document["rows"] if "to" in r)
        for index in range(3000):
            path = host / mover["path"] / "bulk" / f"{index:04d}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"prior note {index}\n", encoding="utf-8")
        planned = self.plan(host)
        digest = roster_digest(planned)
        # A FILE, never a pipe: a roster of thousands of lines fills a pipe nobody drains while
        # this test polls, and the act would stall before its first write -- a kill then
        # measures a blocked process, not an act.
        spoken = open(host.parent / f"{host.name}.takeover.out", "w+b")
        self.addCleanup(spoken.close)
        process = subprocess.Popen(
            [sys.executable, str(CLI), "takeover", "--root", str(host), "--kit", str(KIT),
             "--approve", APPROVER, "--roster", digest],
            stdout=spoken, stderr=subprocess.STDOUT)
        caught, deadline = None, time.monotonic() + 60.0
        while time.monotonic() < deadline:
            record = read_journal(host)
            if record and any(p["id"] == "carry" and p["status"] == "UNSET" for p in record["phases"]):
                caught = record
                break
            if process.poll() is not None:
                break
            time.sleep(0.001)
        alive = process.poll() is None
        process.kill()
        process.wait()
        spoken.seek(0)
        said = spoken.read().decode("utf-8", "replace")[-4000:]
        self.assertIsNotNone(caught, "no journal ever showed the act inside its carry: " + said)
        self.assertTrue(alive, "the act finished before it could be killed; nothing was measured")

        ctx = self._ctx(host)
        self.assertFalse(json.loads((host / acts.record_path(ctx, digest)).read_text("utf-8"))
                         .get("carried_at"), "a killed act declared itself carried")
        self.assertEqual([], self.act_of(host), "the estate accounted for an act that never finished")

        before = tree_of(host)
        held = self.carry(host, digest)
        self.assertEqual(3, held.returncode, "a host held by a dead act was written into")
        self.assertIn("already held", held.stderr)
        resumed = self.plan(host, "--break-lock", APPROVER)
        self.assertIn("INTERRUPTED", resumed)
        self.assertEqual(before, tree_of(host), "reading an interrupted act wrote into the host")

        finished = self.carry(host, digest, "--break-lock", APPROVER)
        self.assertEqual(0, finished.returncode, finished.stderr)
        [act] = self.act_of(host)
        self.assertEqual(digest, act["digest"])
        self.assertEqual(2, len(act["runs"]), "the account does not name both runs that carried it")
        for item in act["roster"]["paths"]:
            self.assertFalse((host / item["path"]).exists(), f"{item['path']} was never carried")
            self.assertEqual(item["digest"], sha(host / item["to"]))
        journal = read_journal(host)
        self.assertEqual(["carry"], journal["resumed_from"]["interrupted_in"])


EFFECT_RELOCATES = {d: acts.succession.EFFECTS[e][1] for d, e in EFFECT.items()}


if __name__ == "__main__":
    unittest.main()
