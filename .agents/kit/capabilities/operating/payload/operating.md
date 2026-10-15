# operating -- how this host routes work, and what comes back

A packet names its DELIVERABLE -- the one thing that will exist when the run ends -- and the two facts a
route is chosen on: how much unmade judgement the task holds, and what a wrong answer costs to undo. The
host's route table (`.agents/project/operating/routes.json`) answers each cell: the role, the adapter,
whether a verification profile is required, the budget and the longest instruction a packet may carry.
A profile is a named argv the port runs in the worker's tree when it returns; no text from a packet is
ever executed. An empty table is a legal state: packets are carried, nothing is judged by their routing
facts, and the port says so on every dispatch.

A worker hands back a RETURN when its adapter declares one of its artifacts `carries` it: what it
delivered or why it refused (an argument, an alternative, who decides), what it cost and what it chose
not to read, what it found beyond its scope, how good its brief was, and what it learned. A declared
return that is missing or does not honour its schema closes the task as failed, by name.
