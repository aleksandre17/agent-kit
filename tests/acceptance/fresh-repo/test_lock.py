"""Acceptance: the lockfile -- what the kit IS, and what it refuses.

The subject is a defect the kit committed against itself. Its whole premise is that every path in
a tree resolves to exactly one declared class; the first time it ran, it dropped bytecode INSIDE
its own payload, and the answer at the time was a `.gitignore` line -- which stops git seeing the
file and stops nobody else. A fence is not a mechanism.

So these tests are about what the kit CANNOT do:

  1. it cannot be, on disk, anything other than what it enumerates -- and the enumeration comes
     from the declarations themselves, not from a hand-kept list;
  2. it cannot ship an unaccounted path: bytecode in the payload is REFUSED and named, and a
     lockfile cannot even be WRITTEN across such a tree, so the record can never be produced over
     a defect and then read afterwards as a clean bill;
  3. it cannot report a changed file as anything but `stale`, and cannot report it without
     stating BOTH moments -- a digest is a reading of a file at an instant and reads afterwards
     exactly like a permanent property of it;
  4. it cannot silently absorb a line-ending translation. This repository has already had a
     byte-reproducibility claim go false the moment it crossed git; a lockfile is precisely where
     that failure returns, so a carriage return is a NAMED state and never a hash mismatch;
  5. it cannot believe a sensor that was pointed at nothing: a ships rule matching no file, a
     rule that would swallow a whole directory, and a path accounted for twice are all refusals.

Every one of these is a MUTATION against a real fixture kit. A lockfile that nothing has ever
failed against is a certificate, not a measurement -- and a certificate is what this slice was
most in danger of producing.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, LOCK, Fixtures, shipped  # noqa: I001 -- sets the interpreter's path

#: The state vocabulary is IMPORTED from the module that owns it. A test spelling its own copy of
#: the words the interpreter prints goes on passing after the interpreter has changed them.
import lockfile  # noqa: E402

RECORDED = json.loads((KIT / LOCK).read_text(encoding="utf-8"))
SHIPS = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))["ships"]

#: A path that is certainly locked, chosen from the record rather than spelled here.
A_LOCKED_FILE = next(entry["path"] for entry in RECORDED["files"]
                     if entry["path"].endswith(".md"))

#: The shape bytecode takes inside the payload. Not a name this suite invented to be convenient:
#: it is what CPython writes, and it is what actually appeared.
BYTECODE = "interpreters/__pycache__/cli.cpython-313.pyc"


def survey(kit, *flags):
    """`lock --plan` over a kit, returned as (exit code, the states it reported by path)."""
    result = Fixtures.run_kit(kit, Fixtures.host(), "lock", "--plan", *flags)
    states = {}
    for line in (result.stdout + result.stderr).splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in lockfile.STATES:
            states[parts[1]] = parts[0]
    return result, states


class Lock(Fixtures, unittest.TestCase):

    # -- 1. the kit is what it says it is -------------------------------------------------
    def test_109_the_kit_on_disk_is_exactly_what_it_enumerates(self):
        """Every path present is accounted for, every path accounted for is present, and every
        digest still holds. This is the standing state, and it is the only assertion here that
        does not mutate -- the ones that follow are what stop it from being a certificate."""
        result, states = survey(KIT)
        self.assertEqual({}, states, "the real kit reports a path it cannot ship")
        self.assertEqual(0, result.returncode)
        self.assertEqual(RECORDED["count"], len(RECORDED["files"]))
        self.assertTrue(RECORDED["taken_at"], "a reading with no moment cannot be contradicted")
        self.assertNotIn(LOCK, [entry["path"] for entry in RECORDED["files"]],
                         "the lock cannot be part of the set it describes")

    def test_110_every_shipped_path_carries_a_class_and_the_rule_that_accounted_for_it(self):
        """A path with no class is the whole defect. There is no entry without one, and each names
        WHICH accounting claimed it, so a reader can ask why any file is in the kit at all."""
        rules = {rule["id"] for rule in SHIPS["accounts"]} | {"declaration-closure"}
        for entry in shipped():
            self.assertTrue(entry["class"], f"{entry['path']}: no class")
            self.assertIn(entry["accounted_by"], rules, f"{entry['path']}: unknown accounting")

    # -- 2. what it refuses to ship ---------------------------------------------------------
    def test_111_bytecode_in_the_payload_is_refused_by_name(self):
        """The original defect, mutated back in. It is not tolerated, not warned about and not
        ignored: it is named `unaccounted`, and the run fails."""
        kit = self.fixture_kit("bytecode", patch=_write(BYTECODE, b"\x00not a declaration"))
        result, states = survey(kit)
        self.assertEqual(lockfile.UNACCOUNTED, states.get(BYTECODE))
        self.assertNotEqual(0, result.returncode)

    def test_112_a_lockfile_cannot_be_written_across_an_unaccounted_path(self):
        """The half that matters. If generation ignored what it could not account for, the record
        would be produced over the defect and read forever after as a clean bill -- a certificate
        signed by the thing it certifies. The apply run refuses, and leaves the record untouched."""
        kit = self.fixture_kit("no-blessing", patch=_write(BYTECODE, b"\x00"))
        before = (kit / LOCK).read_bytes()
        result = self.run_kit(kit, self.host(), "lock")
        self.assertNotEqual(0, result.returncode)
        self.assertIn(lockfile.UNACCOUNTED, result.stdout + result.stderr)
        self.assertEqual(before, (kit / LOCK).read_bytes(),
                         "a refused generation still rewrote the record")

    def test_113_a_file_that_moved_since_the_lock_is_stale_and_both_moments_are_stated(self):
        """A digest is a reading taken at an instant. When two readings disagree, the report says
        WHEN each was taken rather than announcing which one is now true."""
        kit = self.fixture_kit("moved", patch=_append(A_LOCKED_FILE, "\na line nobody locked\n"))
        result, states = survey(kit)
        self.assertEqual(lockfile.STALE, states.get(A_LOCKED_FILE))
        self.assertIn(RECORDED["taken_at"], result.stdout,
                      "the report never says when the reading it disagrees with was taken")
        self.assertNotEqual(0, result.returncode)

    def test_114_a_locked_file_that_is_gone_is_missing_not_merely_different(self):
        kit = self.fixture_kit("gone", patch=_remove(A_LOCKED_FILE))
        result, states = survey(kit)
        self.assertEqual(lockfile.MISSING, states.get(A_LOCKED_FILE))
        self.assertNotEqual(0, result.returncode)

    def test_115_a_carriage_return_is_named_as_a_translation_never_as_a_mismatch(self):
        """The boundary this repository has already been burned by. A file rewritten with CRLF has
        a different digest, so the cheap answer would be `stale` -- and `stale` would send whoever
        read it to look for an edit that never happened. The kit measures the bytes instead and
        reports the translation, which is the only reading that leads anywhere."""
        kit = self.fixture_kit("crlf", patch=_crlf(A_LOCKED_FILE))
        result, states = survey(kit)
        self.assertEqual(lockfile.LINE_ENDINGS, states.get(A_LOCKED_FILE))
        self.assertNotEqual(lockfile.STALE, states.get(A_LOCKED_FILE))
        self.assertNotEqual(0, result.returncode)

    # -- 3. a sensor proves it was pointed at something --------------------------------------
    def test_116_a_ships_rule_that_matches_nothing_is_refused(self):
        """An attribution that cannot fail does not measure, it certifies. A rule over an empty
        set passes gloriously and reads exactly like a scan that looked and found nothing."""
        kit = self.fixture_kit("empty-rule", patch=_rule(
            {"id": "nothing", "class": "interpreter", "root": "interpreters/", "suffix": ".ts"}))
        result, _states = survey(kit)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("matched no file", result.stderr)

    def test_117_a_rule_over_a_directory_must_state_what_it_accounts_for(self):
        """The defect's own escape route, closed. A rule that swallowed a directory whole would
        have accounted for the bytecode too, and the cure would have shipped the disease."""
        kit = self.fixture_kit("greedy-rule", patch=_rule(
            {"id": "everything", "class": "interpreter", "root": "interpreters/"}))
        result, _states = survey(kit)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("states no suffix", result.stderr)

    def test_118_one_path_accounted_for_twice_is_a_name_with_two_meanings(self):
        """Refused here rather than settled by a precedence ladder somewhere else."""
        kit = self.fixture_kit("twice", patch=_rule(
            {"id": "again", "class": "prose", "root": "fitness/", "suffix": ".json"}))
        result, _states = survey(kit)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("accounted for twice", result.stderr)


# -- the mutations, each one the proof that the sensor above it can go red ---------------------
def _write(rel: str, body: bytes):
    def patch(kit):
        target = kit / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    return patch


def _append(rel: str, text: str):
    def patch(kit):
        with open(kit / rel, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return patch


def _remove(rel: str):
    return lambda kit: (kit / rel).unlink()


def _crlf(rel: str):
    """The same content, translated. Nothing about the file's meaning changed, which is exactly
    why a report that called this `stale` would be sending a reader after a ghost."""
    def patch(kit):
        target = kit / rel
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    return patch


def _rule(rule: dict):
    return lambda kit: Fixtures.edit_json(
        kit, "MANIFEST.json", lambda value: value["ships"]["accounts"].append(rule))
