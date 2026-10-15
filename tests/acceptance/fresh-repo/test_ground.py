"""Acceptance: a ground is a reading with an expiry, not a fact (ADR-022 decision 4, slice S2).

The prior system measured the waste: in:out near 100:1, almost all of it SEARCHING -- runs re-mapping
ground another run had already mapped, and a router briefing a worker with hours-old facts. The cure
is a ledger in which a fact is recorded with the instrument that produced it and the narrowest paths
it depends on, and is returned only while those paths hold what they held. Held here:

  1. a recorded fact is read back while its paths are unchanged -- and an edit ELSEWHERE does not
     expire it;
  2. an edit to a declared path turns the read into a DECLARED MISS (its own exit code) that names
     the path and hands back the instrument;
  3. a fact without an instrument, or without a path to expire with, is refused and nothing is kept;
  4. a file the repository does not carry never moves a reading.

Every code and place is read from the module that owns it.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from harness import CLI, KIT, Fixtures

import readings

VERB = "ground"


class Ground(Fixtures, unittest.TestCase):

    def grounded(self, host: Path, *flags):
        result = subprocess.run([sys.executable, str(CLI), VERB, "--root", str(host), "--kit", str(KIT), *flags],
                                capture_output=True, text=True)
        print(f"\n$ {VERB} {' '.join(flags)}\n[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    def a_host_with_two_places(self) -> Path:
        host = self.installed()
        for rel in ("measured/one.txt", "elsewhere/two.txt"):
            (host / rel).parent.mkdir(parents=True, exist_ok=True)
            (host / rel).write_text("as it was\n", encoding="utf-8", newline="\n")
        return host

    def test_370_a_fact_holds_while_its_paths_do_and_an_edit_elsewhere_does_not_expire_it(self):
        host = self.a_host_with_two_places()
        said = self.grounded(host, "--key", "files-measured", "--fact", "one file, unchanged",
                             "--instrument", "ls measured", "--path", "measured")
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        (host / "elsewhere/two.txt").write_text("moved\n", encoding="utf-8")
        read = self.grounded(host, "--key", "files-measured")
        self.assertEqual(0, read.returncode, read.stdout + read.stderr)
        self.assertIn("one file, unchanged", read.stdout)

    def test_371_an_edit_to_a_declared_path_is_a_declared_miss_that_hands_back_the_instrument(self):
        host = self.a_host_with_two_places()
        self.grounded(host, "--key", "files-measured", "--fact", "one file", "--instrument", "ls measured",
                      "--path", "measured")
        (host / "measured/one.txt").write_text("moved\n", encoding="utf-8")
        read = self.grounded(host, "--key", "files-measured")
        self.assertEqual(readings.GroundMiss.exit_code, read.returncode, read.stdout + read.stderr)
        self.assertIn(f"[{readings.GroundMiss.code}]", read.stderr)
        self.assertIn("measured", read.stderr)
        self.assertIn("ls measured", read.stderr)
        never = self.grounded(host, "--key", "never-measured")
        self.assertEqual(readings.GroundMiss.exit_code, never.returncode)

    def test_372_a_fact_without_its_instrument_or_its_paths_is_refused_and_nothing_is_kept(self):
        host = self.a_host_with_two_places()
        for flags in (["--key", "k", "--fact", "f", "--path", "measured"],
                      ["--key", "k", "--fact", "f", "--instrument", "ls"]):
            with self.subTest(flags=flags):
                said = self.grounded(host, *flags)
                self.assertNotEqual(0, said.returncode)
                self.assertIn(f"[{readings.GroundRefused.code}]", said.stderr)
        self.assertEqual(readings.GroundMiss.exit_code, self.grounded(host, "--key", "k").returncode)

    def test_373_a_file_the_repository_does_not_carry_never_moves_a_reading(self):
        host = self.a_host_with_two_places()
        (host / ".gitignore").write_text("measured/scratch/\n", encoding="utf-8", newline="\n")
        self.grounded(host, "--key", "files-measured", "--fact", "one file", "--instrument", "ls measured",
                      "--path", "measured")
        (host / "measured/scratch").mkdir()
        (host / "measured/scratch/build-output.txt").write_text("noise\n", encoding="utf-8")
        self.assertEqual(0, self.grounded(host, "--key", "files-measured").returncode)


if __name__ == "__main__":
    unittest.main()
