"""Run a kit verb from the host root, through the kit this host runs: its pinned copy, or -- in a
referenced host -- the kit its lock references in the host's own tree. Arguments pass through."""
import json
import subprocess
import sys
from pathlib import Path

kit, lock = Path(".agents/kit"), Path(".agents/project/kit.lock.json")
if lock.is_file():
    kit = Path((json.loads(lock.read_text(encoding="utf-8")).get("reference") or {}).get("path") or kit)
cli = kit / "interpreters" / "cli.py"
if not cli.is_file():
    sys.exit(f"no kit at {kit.as_posix()} -- run this from the host root"
             + ("" if kit == Path(".agents/kit") else "; an uninitialised submodule: git submodule update --init"))
sys.exit(subprocess.call([sys.executable, "-I", "-B", str(cli), *sys.argv[1:2], "--root", ".", *sys.argv[2:]]))
