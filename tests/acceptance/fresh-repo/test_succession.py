"""ADR-011 -- reading a host's PRIOR agent system: the machine takes the census and measures, a
signed migration map declares, and a path no row answers is `undecided`, never defaulted.

Every host here is a scratch repository with the FIXTURE prior system copied in; the real second
host is never read from a test. Every state is derived from the declared vocabulary, never
restated: a test holding its own list of dispositions goes on passing after the kit changes them.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import unittest
from pathlib import Path

from harness import FIXTURES, KIT, Fixtures, host_digest

PRIOR = FIXTURES / "prior-system"
TREE = PRIOR / "tree"
MAP = PRIOR / "map.json"
MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))


def _vocabulary_home(kit: Path = KIT):
    """(the capability declaration path, the vocabulary path) -- asked of the declarations."""
    for entry in json.loads((kit / "MANIFEST.json").read_text(encoding="utf-8"))["capabilities"]:
        declaration = json.loads((kit / entry["declaration"]).read_text(encoding="utf-8"))
        for document in declaration.get("documents", []):
            if document["validates"] == "succession":
                return entry["declaration"], document["source"]
    raise AssertionError("no capability declares a succession vocabulary")


VOCABULARY = json.loads((KIT / _vocabulary_home()[1]).read_text(encoding="utf-8"))
DISPOSITIONS = [d["id"] for d in VOCABULARY["dispositions"]]
UNDECIDED = VOCABULARY["undecided"]["id"]
STATES = DISPOSITIONS + [UNDECIDED]
MAP_ROWS = json.loads(MAP.read_text(encoding="utf-8"))["rows"]
FIXTURE_PATHS = sorted(p.relative_to(TREE).as_posix() for p in TREE.rglob("*") if p.is_file())


def roster(stdout: str, states=None) -> dict:
    """path -> (state, the rest of the line)."""
    states = STATES if states is None else states
    found = {}
    for line in stdout.splitlines():
        match = re.match(r"^  (\S+)  (\S+)(.*)$", line)
        if match and match.group(1) in states:
            found[match.group(2)] = (match.group(1), match.group(3))
    return found


def counts(stdout: str) -> dict:
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^  count  (\S+) = (\d+)$", stdout, re.M)}


def refusal_code(stderr: str):
    match = re.search(r"^kit: \[(\w+)\] ", stderr, re.M)
    return match.group(1) if match else None


class SuccessionTests(Fixtures, unittest.TestCase):

    def prior_host(self) -> Path:
        host = self.host()
        shutil.copytree(TREE, host, dirs_exist_ok=True)
        return host

    def a_map(self, mutate=None) -> Path:
        document = json.loads(MAP.read_text(encoding="utf-8"))
        if mutate:
            mutate(document)
        target = self._temp("kit-map-") / "map.json"
        target.write_text(json.dumps(document, indent=2), encoding="utf-8")
        return target

    def read(self, host: Path, map_file=None, kit: Path = KIT):
        before = host_digest(host)
        flags = ("--map", str(map_file)) if map_file else ()
        result = self.run_kit(kit, host, "inherit", *flags)
        self.assertEqual(before, host_digest(host), "a READING changed the host it read")
        return result

    def refused(self, mutate) -> str:
        result = self.read(self.prior_host(), self.a_map(mutate))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(refusal_code(result.stderr), "KIT0036", result.stderr)
        self.assertEqual(roster(result.stdout), {}, "a refused map still printed a roster")
        return result.stderr

    # -- the census --------------------------------------------------------------------------
    def test_231_without_a_map_the_census_is_only_the_kits_own_declared_boundary_and_no_prior_path_is_read(self):
        self.assertTrue(FIXTURE_PATHS)
        result = self.read(self.prior_host())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(roster(result.stdout), {})
        self.assertEqual(counts(result.stdout), {**{s: 0 for s in STATES}, "census": 0})
        for plane in MANIFEST["planes"]:
            self.assertIn(f"  boundary  {plane['root'].rstrip('/')}  0 path(s)", result.stdout)

    def test_232_with_a_map_every_path_under_a_declared_prior_root_is_in_the_census_exactly_once_and_every_state_is_counted_zeros_included(self):
        result = self.read(self.prior_host(), MAP)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(roster(result.stdout)), FIXTURE_PATHS)
        tally = counts(result.stdout)
        self.assertEqual(set(tally), set(STATES) | {"census"})
        self.assertEqual(sum(tally[s] for s in STATES), tally["census"])
        self.assertEqual(tally["census"], len(FIXTURE_PATHS))

    def test_233_a_path_no_row_answers_is_undecided_named_and_the_reading_says_it_is_incomplete(self):
        result = self.read(self.prior_host(), MAP)
        unanswered = [p for p in FIXTURE_PATHS
                      if not any(p == r["path"] or p.startswith(r["path"] + "/") for r in MAP_ROWS)]
        self.assertTrue(unanswered)
        found = roster(result.stdout)
        for path in unanswered:
            self.assertEqual(found[path][0], UNDECIDED)
        self.assertIn("INCOMPLETE", result.stdout)

    def test_234_the_most_specific_row_answers_a_path_and_a_directory_row_carries_the_remainder_below_its_destination(self):
        nested = [r for r in MAP_ROWS if any(o["path"] != r["path"] and r["path"].startswith(o["path"] + "/")
                                             and o["disposition"] != r["disposition"] for o in MAP_ROWS)]
        self.assertTrue(nested)
        found = roster(self.read(self.prior_host(), MAP).stdout)
        for row in nested:
            below = [p for p in FIXTURE_PATHS if p.startswith(row["path"] + "/")]
            self.assertTrue(below)
            for path in below:
                self.assertEqual(found[path][0], row["disposition"])
                if "to" in row:
                    self.assertIn(f"to={row['to']}{path[len(row['path']):]}", found[path][1])

    def test_235_bytes_identical_to_kit_payload_are_measured_as_evidence_and_never_assign_a_disposition(self):
        host = self.prior_host()
        stray = [p for p in FIXTURE_PATHS if not any(p.startswith(r["path"]) for r in MAP_ROWS)]
        self.assertTrue(stray)
        source = _vocabulary_home()[1]
        copy = f"{stray[0].rsplit('/', 1)[0]}/copy-of-kit-bytes.json"
        shutil.copyfile(KIT / source, host / copy)
        found = roster(self.read(host, MAP).stdout)
        self.assertEqual(found[copy][0], UNDECIDED)
        self.assertIn(f"byte-identical to kit {source}", found[copy][1])

    @unittest.skipUnless(sys.platform == "win32" or hasattr(os, "symlink"), "no link primitive")
    def test_236_a_link_in_the_prior_system_is_one_path_and_is_never_walked_through(self):
        host = self.prior_host()
        referent = host / "elsewhere"
        (referent / "inner").mkdir(parents=True)
        (referent / "inner" / "secret.md").write_text("behind a link\n", encoding="utf-8")
        link = host / "legacy-agents" / "linked"
        if sys.platform == "win32":
            import _winapi
            _winapi.CreateJunction(str(referent), str(link))
        else:
            os.symlink(referent, link, target_is_directory=True)
        found = roster(self.read(host, MAP).stdout)
        self.assertIn("legacy-agents/linked", found)
        self.assertIn("a link to", found["legacy-agents/linked"][1])
        self.assertFalse([p for p in found if p.startswith("legacy-agents/linked/")])

    # -- the map is refused WHOLE when it says what it cannot mean --------------------------
    def test_237_a_row_naming_an_undeclared_disposition_or_the_unanswered_state_itself_is_refused_whole(self):
        for word in ("not-a-declared-disposition", UNDECIDED):
            stderr = self.refused(lambda d, w=word: d["rows"].append({"path": "legacy-agents/stray.txt", "disposition": w}))
            self.assertIn(repr(word), stderr)

    def test_238_a_row_missing_or_adding_a_field_its_disposition_declares_is_refused_whole(self):
        carrying = next(d for d in VOCABULARY["dispositions"] if d["carries"])
        field = carrying["carries"][0]["field"]
        self.assertIn(field, self.refused(lambda d: d["rows"].append(
            {"path": "legacy-agents/stray.txt", "disposition": carrying["id"]})))
        self.assertIn("carries no 'surplus'", self.refused(lambda d: d["rows"].append(
            {"path": "legacy-agents/stray.txt", "disposition": carrying["id"],
             **{c["field"]: "legacy text" for c in carrying["carries"]}, "surplus": "x"})))

    def test_239_every_declared_reference_kind_is_checked_and_a_value_naming_nothing_is_refused(self):
        kinds = {c["refers"]: (d["id"], c["field"]) for d in VOCABULARY["dispositions"] for c in d["carries"]}
        self.assertTrue(kinds)
        for kind, (disposition, field) in kinds.items():
            wrong = "   " if kind == "statement" else "outside-every-plane/and-no-capability"
            stderr = self.refused(lambda d, di=disposition, f=field: d["rows"].append(
                {"path": "legacy-agents/stray.txt", "disposition": di, f: wrong}))
            self.assertIn(f"{field} --", stderr, kind)

    def test_240_two_rows_for_one_path_or_two_paths_sent_to_one_destination_are_refused_whole(self):
        self.assertIn("a second row for the same path", self.refused(
            lambda d: d["rows"].append(dict(d["rows"][0]))))
        mover = next(r for r in MAP_ROWS if "to" in r)
        onto_one = [{"path": path, "disposition": mover["disposition"], "to": mover["to"] + "/one"}
                    for path in ("legacy-agents/stray.txt", "LEGACY-SYSTEM.md")]

        def two_onto_one(document):
            document["rows"] = [r for r in document["rows"] if r["path"] != "LEGACY-SYSTEM.md"] + onto_one

        self.assertIn("more than one path to one place", self.refused(two_onto_one))

    def test_241_a_prior_root_or_row_that_leaves_the_host_is_refused_whole(self):
        self.assertIn("not a path inside this host", self.refused(lambda d: d["prior"].append("../outside")))
        self.assertIn("not a path inside this host", self.refused(
            lambda d: d["rows"].__setitem__(0, {**d["rows"][0], "path": "../legacy"})))

    # -- the vocabulary grows by declaration ------------------------------------------------
    def test_242_a_new_disposition_is_a_declaration_in_the_vocabulary_and_the_interpreter_reads_it_unchanged(self):
        source = _vocabulary_home()[1]
        kit = self.fixture_kit("archived", patch=lambda k: self.edit_json(k, source, lambda v: v["dispositions"].append(
            {"id": "archived", "says": "kept outside the kit, read-only", "carries": [{"field": "because", "refers": "statement"}]})))
        map_file = self.a_map(lambda d: d["rows"].append(
            {"path": "legacy-agents/stray.txt", "disposition": "archived", "because": "history"}))
        result = self.read(self.prior_host(), map_file, kit=kit)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(roster(result.stdout, STATES + ["archived"])["legacy-agents/stray.txt"][0], "archived")
        self.assertEqual(counts(result.stdout)["archived"], 1)

    def test_243_a_vocabulary_referring_to_a_kind_no_interpreter_can_check_is_refused_never_ignored(self):
        source = _vocabulary_home()[1]
        kit = self.fixture_kit("unknown-kind", patch=lambda k: self.edit_json(k, source, lambda v: v["dispositions"].append(
            {"id": "sent", "says": "sent away", "carries": [{"field": "to", "refers": "a-kind-nobody-checks"}]})))
        result = self.read(self.prior_host(), MAP, kit=kit)
        self.assertEqual(refusal_code(result.stderr), "KIT0036", result.stderr)
        self.assertIn("a-kind-nobody-checks", result.stderr)


if __name__ == "__main__":
    unittest.main()
