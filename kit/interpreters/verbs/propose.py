"""propose -- what this host learned that it says is not its own, as text a person carries.

A framework cannot learn from the repositories it is installed in unless somebody carries what
they found back to it. This verb is that carriage and nothing more: it reads what the host has
already written down, and where a claim has been made twice about the world beyond this
repository, it PRINTS a proposal addressed to whoever published the framework.

Three refusals are built into the shape of it, and each is the answer to a way this goes wrong:

  * **It carries nothing.** No network is opened, no publisher is contacted, nothing is written
    anywhere -- inside this host or outside it. The output is text on a stream. A host that could
    post its findings upstream would have acquired a dependency on its framework that nobody
    declared and nobody could see; and the first outage of whatever it posted to would become an
    outage of the host's own tooling.

  * **It happens only when asked.** Nothing schedules it, no hook fires it, no other verb calls
    it, and no judgement of this host's health mentions it. That is deliberate and it is the
    whole difference between a proposal and a telemetry stream: a machine that decided when to
    send somebody else's lessons on would be deciding, on the host's behalf, what the host had
    to say about itself.

  * **It refuses on one occasion.** A claim asked for by name that has been made once is refused,
    and the refusal says what is missing rather than printing something weaker. One occasion is
    an observation; the second is the point at which a project is provably paying for it twice.
    How many occasions a word needs is declared beside that word by whoever published it -- this
    verb holds no number, and would print nothing at all under a word that declares none.

Asked with no subject it is a REPORT: everything ready to carry, printed whole, and everything
withheld, named with what it lacks. A host that has marked nothing says so and exits zero --
having nothing to send is the ordinary state of an honest repository, not a finding.
"""

from __future__ import annotations

import lesson
from errors import KitError

SUMMARY = "state what this host learned that it says is not its own, as text a person carries"
MUTATES = False
REQUIRES_APPROVED_HOST = True

#: How the text marks its own edges, so a reader can see where one proposal ends and tell a
#: pasted fragment from a whole one.
RULE = "-" * 88


class ProposeError(KitError):
    """What was asked for cannot be carried: nothing here has said it, or it has been said once."""

    code = "KIT0067"


def _occasions(standing) -> str:
    lines = []
    for index, seen in enumerate(standing.seen, start=1):
        lines.append(f"  {index}. {seen.identity} -- {seen.title!r}")
        lines.append(f"     written at: {seen.where}")
        lines.append(f"     state: {seen.state} ({seen.state_title}) -- {seen.state_intent!r}")
        lines.append(f"     the lifecycle this host declares leads no passage out of that state, "
                     f"so the work is over and this is what it taught")
    return "\n".join(lines)


def proposal(standing, reading) -> str:
    """One claim, written as the party it is addressed to would receive it.

    Every word in it that is the host's own arrives WITH the declaration that gives it meaning --
    the mark with the sentence its publisher wrote for it, the state with the intent its lifecycle
    declares, each occasion with the path it can be opened at. A text that quoted the host's words
    and left them to be interpreted would be asking its reader to learn a vocabulary in order to
    read a proposal about their own framework.
    """
    statements = "\n".join(
        f"  {seen.statement!r}\n     -- {seen.identity} ({seen.where})" for seen in standing.seen)
    return f"""{RULE}
A PROPOSAL FROM A HOST TO WHOEVER PUBLISHED ITS FRAMEWORK
subject: {standing.subject}
{RULE}

  Nothing was sent. This text was produced because somebody asked for it, by a machine that
  opened no connection and wrote nothing anywhere -- inside this repository or outside it. It
  travels only if a person carries it, and if nobody does, nothing has happened.

WHAT THE HOST SAYS IT LEARNED
{statements}

HOW FAR THE HOST CLAIMS IT HOLDS
  Every record above marks this {standing.mark!r}, and the vocabulary that word was published in
  declares that word as:
  {standing.row[lesson.MEANS]!r}

ON WHAT OCCASIONS IT WAS SEEN ({len(standing.seen)}; a claim under this word may be carried \
at {standing.bar})
{_occasions(standing)}

WHAT IS BEING ASKED
  That whoever publishes this framework decide whether this belongs in it, and record the
  decision where their decisions live. Declining is a complete answer, and so is adopting
  something narrower than what is claimed here. Nothing is owed, nothing is installed by this
  text, and the host is not waiting on it: the host has already acted on what it learned, which
  is why there are records to quote.

HOW TO READ THIS WITHOUT KNOWING THE HOST
  Every word above that belongs to the host is quoted beside the declaration that gives it
  meaning, so nothing here has to be looked up in a vocabulary the reader does not have. What
  does need the host is the PATHS -- they are carried so that a reader who doubts any line of
  this can open the record it came from rather than take this text's word for it.

  Read at {reading.taken_at}. The records said this at that moment, and reading them did not
  change one of them.
{RULE}"""


def _refuse_unread(reading) -> None:
    raise ProposeError(
        "no capability this host has enabled declares anywhere for a record to say what its work "
        "taught, so nothing here could have been marked and nothing was read. This is an unread "
        "question and not an empty answer: enable something that holds such records, or address "
        "the proposal to its publisher in your own words, which nothing here forbids")


def _refuse_unknown(reading, subject: str) -> None:
    about = reading.about(subject)
    if not about:
        raise ProposeError(
            f"nothing in this host says anything about {subject!r}; what has been written about "
            f"is {reading.named()}. A text produced for a subject nobody wrote about would be "
            f"this machine composing a finding on the host's behalf")
    marks = sorted({seen.mark for seen in about})
    raise ProposeError(
        f"{subject!r} is written about here, on {len(about)} record(s), and none of them claims "
        f"it holds beyond this repository: the word(s) used are {marks}, and of the words "
        f"published here only "
        f"{sorted(name for name, row in reading.words.items() if row[lesson.BEYOND])} say a claim "
        f"reaches past the host that made it. What was learned here may be entirely true and "
        f"still be nobody else's business -- that is what those records are saying, and carrying "
        f"it anyway would be overruling them")


def _one(ctx, reading, subject: str) -> int:
    standings = reading.of(subject)
    if not standings:
        _refuse_unknown(reading, subject)
    ready = [standing for standing in standings if standing.carried]
    if not ready:
        raise ProposeError(
            f"{subject!r} is claimed to hold beyond this repository and is not carried yet -- "
            + "; ".join(standing.missing() for standing in standings)
            + ". Nothing was written and nothing was sent"
        )
    for standing in ready:
        print(proposal(standing, reading))
    return 0


def _all(ctx, reading) -> int:
    ready = [standing for standing in reading.standings if standing.carried]
    for standing in ready:
        print(proposal(standing, reading))
    withheld = [standing for standing in reading.standings if not standing.carried]
    for standing in withheld:
        print(f"propose: WITHHELD  {standing.subject} -- {standing.missing()}")
    for note in reading.unreadable:
        print(f"propose: UNREAD  {note}")
    if not ready and not withheld:
        print("propose: no record here claims to have learned anything that holds beyond this "
              "repository. That is a complete state and an ordinary one -- a host with nothing "
              "to send is not a host that failed to send something, and nothing here will "
              "manufacture a proposal to fill the silence.")
    else:
        print(f"propose: {len(ready)} proposal(s) ready to carry, {len(withheld)} withheld. "
              f"Nothing was sent and nothing was written: a person carries this text, or it "
              f"does not travel.")
    return 0


def run(ctx, args) -> int:
    reading = lesson.read(ctx)
    subject = getattr(args, "lesson", None)
    if reading.unread:
        if subject:
            _refuse_unread(reading)
        print("propose: nothing this host has enabled declares anywhere for a record to say what "
              "its work taught, so there was no question to ask. Nothing was read, and nothing is "
              "claimed in either direction.")
        return 0
    return _one(ctx, reading, subject) if subject else _all(ctx, reading)
