"""Run a kit verb with --plan from the host root, through the host's pinned kit."""
import subprocess
import sys
from pathlib import Path

cli = Path(".agents/kit/interpreters/cli.py")
if not cli.is_file():
    sys.exit("no pinned kit at .agents/kit -- run this from the host root")
sys.exit(subprocess.call([sys.executable, "-I", "-B", str(cli), *sys.argv[1:2], "--root", ".", *sys.argv[2:], "--plan"]))
