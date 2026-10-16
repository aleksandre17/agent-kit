# Policies -- edit gates published beside the kit, written once for every host

Each directory here is ONE complete capability whose documents keep an enforcement contract (`edit-gate`,
`message-rules`, ...). The enforcement capability reads every such document an enabled capability ships, so a host that takes a
policy is held to its gates at every edit and every commit, exactly as to its own -- and the policy is
written once for all hosts instead of copied into each. A host keeps its own gates, in its own words,
for what only it knows.

    python .agents/kit/interpreters/cli.py take --root . --path policies/<id> --approve <who>

then enable `<id>` in `.agents/project/project.json` and `init --approve <who>`, or take it with a
starter. A host never edits a policy where it landed; its publisher replaces it with a new version.

| policy | what it refuses |
| --- | --- |
| `secrets` | private keys; cloud access key ids; platform tokens (GitHub, GitLab, Slack, API keys of the `sk-` form) -- the one secrets catalogue other tools read by path (`secrets/README.md`) |
| `conventional-commits` | a commit message whose header is not Conventional Commits 1.0.0 (opt-in; the commit-message hook) |
