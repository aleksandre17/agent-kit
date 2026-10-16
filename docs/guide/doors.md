# Doors

Some verbs decide something only a person may decide. Such a verb stops at a **door**: it prints
what it would do and exits 3 ("this is a DOOR"). A door is walked by naming who decides:

```text
<verb> ... --plan               # see exactly what the door decides
<verb> ... --approve <who>      # walk it; the name is recorded on the act
```

Doors include `start`, `take`, `extend`, `upgrade`, `activate`, `retake`, `eject`, `takeover` and
moving a card.

A machine never approves a door. An agent may walk one only when the owner has delegated it in
writing, and it records the delegation as the name, for example
`claude(owner-delegated:<date>)`.
