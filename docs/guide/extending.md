# Extending: extension points

A host never edits the kit. It adds its own files through a declared **extension point**: a
template the kit scaffolds on demand into a host path. The answers only the host can give are
marked `pending`, and `check` reports them until they are answered.

```text
python <kit>/kit/interpreters/cli.py extend --root <host> --list
python <kit>/kit/interpreters/cli.py extend --root <host> --point <id> [--name <n>] --approve <who>
```

Points include:

- the host's laws and norms, and scoped laws;
- skills and skill chapters;
- MCP servers and evals;
- edit gates and known violations;
- owners and the memory contract.

**When a kit template changes,** `extend --merge` brings the change into the host's file with a
three-way merge. A conflict is reported, never overwritten.

**A file in a place a point owns, but declared by no point,** is reported.
