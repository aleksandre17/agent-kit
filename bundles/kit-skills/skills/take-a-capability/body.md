# Take a capability

Taking is mechanical: the verbs do every step. Run, in order, from the host root:

1. `python .agents/kit/interpreters/cli.py take --root . --path <published dir> --plan`
2. Hand the plan to the owner; they run the same command with `--approve <name>` (a door: see `walk-a-door`).
3. `python .agents/kit/interpreters/cli.py retake --root . --approve <name>` if the capability brings a detector, then `render` and `check`.
