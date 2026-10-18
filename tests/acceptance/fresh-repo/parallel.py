"""Run the acceptance suite one MODULE per process, several at a time -- the same tests, judged the same
way, in a fraction of the wall time.

    python -I -B tests/acceptance/fresh-repo/parallel.py [--workers N] [--logs DIR] [module ...]

Every module is its own `unittest` run in its own interpreter, so no state can leak between modules
that a serial run would have shared; every host a test makes is already its own temporary directory.
The verdict is the conjunction of the modules' verdicts, printed per module with its count and its
time, and each module's whole output is kept in `--logs` so a failure is read where it happened.
`-B` is not optional: an interpreter that wrote bytecode into the kit would make the kit differ from
its own lock, and every test that pins it would fail for a reason that has nothing to do with it.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAN = re.compile(r"^Ran (\d+) tests? in", re.M)
#: Every test unittest names as failed or errored, by its own banner.
FAILURE = re.compile(r"^(?:FAIL|ERROR): (\S+)", re.M)
#: The most of one failed module's report printed, in characters: enough for a traceback, never a flood.
REPORT = 6000


def _one(module: Path, logs: Path) -> tuple:
    started = time.monotonic()
    done = subprocess.run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", str(HERE),
                           "-p", module.name], cwd=HERE, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    said = done.stdout + done.stderr
    (logs / f"{module.stem}.log").write_text(said, encoding="utf-8")
    ran = RAN.search(said)
    # A module that deliberately holds no test (a shim discovery imports) ends `NO TESTS RAN`, exit 5:
    # an honest zero, not a failure -- and only when the output says exactly that.
    code = 0 if done.returncode == 5 and "NO TESTS RAN" in said else done.returncode
    return module.stem, code, int(ran.group(1)) if ran else 0, time.monotonic() - started


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--logs", default=None)
    parser.add_argument("modules", nargs="*")
    args = parser.parse_args(argv)
    logs = Path(args.logs or tempfile.mkdtemp(prefix="acceptance-logs-"))
    logs.mkdir(parents=True, exist_ok=True)
    modules = [HERE / (m if m.endswith(".py") else f"{m}.py") for m in args.modules] \
        or sorted(HERE.glob("test_*.py"))
    started = time.monotonic()
    failed, total = [], 0
    # Longest first (Graham's LPT rule): a long module started last is the whole run's tail. A
    # module's size is the stateless stand-in for its length -- the runner keeps no prior timings.
    modules.sort(key=lambda m: m.stat().st_size, reverse=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        # Printed as each module ENDS, so a finished module is never held behind a slower one.
        for done in concurrent.futures.as_completed([pool.submit(_one, m, logs) for m in modules]):
            name, code, ran, took = done.result()
            total += ran
            print(f"  {'OK  ' if code == 0 else 'FAIL'}  {name:<28} {ran:>3} test(s)  {took:6.1f}s", flush=True)
            if code != 0:
                failed.append(name)
    print(f"acceptance: {total} test(s) in {len(modules)} module(s), {time.monotonic() - started:.0f}s, "
          f"{args.workers} worker(s); logs at {logs}")
    if failed:
        # A log kept on a machine nobody can open (a CI runner) is not read where the failure happened:
        # each failed module's own report -- unittest's from its first failure banner -- is printed too.
        for name in failed:
            said = (logs / f"{name}.log").read_text(encoding="utf-8")
            start = said.find("=" * 70)
            # Every failed test by name, before a report that may be cut: one cut report must not
            # read as one failure.
            names = FAILURE.findall(said)
            print(f"\n----- {name} -- {len(names)} failed: {', '.join(names) or 'see the log'} -----\n"
                  f"{(said[start:] if start >= 0 else said)[:REPORT]}")
        print(f"acceptance: FAILED in {len(failed)} module(s): {', '.join(failed)}")
        return 1
    print("acceptance: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
