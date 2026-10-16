# Refusals

A refusal is a decision, not an obstacle (rule `engineering@1.1.1#a-refusal-is-final`). Remove its
cause and ask again through the same door. Never retry through another tool, another path or another
agent.

| Message | Meaning | Do |
|---|---|---|
| `judge: REFUSED <path> <gate>` | the edit introduces text a gate forbids | change the text; the message names the alternative |
| `KIT0083 ... not the kit this host's lock pins` | a referenced kit moved or was edited | restore it, or pin the new commit with `upgrade --mode referenced` |
| `KIT0005 rule ... declared by both ...` | one rule has two homes | keep one |
| `KIT0032 drifted <capability>` | a publisher changed bytes under the same version | the publisher releases a new version; the host takes it (a referenced host: `upgrade --mode referenced --approve <who>`) |
| `KIT0007 ... this is a DOOR` | a decision for the owner | run `--plan`, then `--approve <who>` |
| `spawn: REFUSED -- the brief lacks ...` | a sub-agent brief is not a packet | write MISSION, GROUND, BOUNDARIES, RETURN, BUDGET |
| `NT-UNENFORCED`, `NT-CONTRADICTS`, `NT-LOOSENED` | the normative tree is incoherent | name an enforcer the host has (a gate, an edit gate, a verb, or an adapter's, like `stack-kit:test`), resolve the contradiction, or declare the exception |
| `FF-READING-FRESH` | the host's measured reading moved | run `retake --plan`, then `retake --approve <who>` |

The diagnostics registry (`kit/diagnostics.json`) lists every KIT code and what it means.
