"""The boundary declaration, READ -- the machinery behind ADR-001's T1, T2 and T3.

Held apart from any suite, like the harness, and for the same reason: nothing here asserts. It
reads `tests/acceptance/fresh-repo/boundary.json`, points each declared rule at each declared scope, and returns
findings. Which rules exist, what they catch, what they tolerate and which hosts they are measured
across are all in the declaration; a rule added there is measured by the existing tests, and a new
WAY of measuring is a class in `KINDS` -- never an edit to a test.

Three things in here are load-bearing and easy to lose:

  1. **Calibration before scan.** Every rule carries one specimen it must flag and one it must
     admit. If a rule cannot do both, nothing is scanned on its word and the rule is the finding.
     A detector believed before it was measured is how a system acquires confident readings of a
     world it was never pointed at.
  2. **What an interpreter may legitimately name.** Not "no proper nouns" -- that question is
     narrower than the one that matters. A machine may name a term its SCHEMAS declare (the
     contract between a declaration and its reader) and a term it PROVIDES as an extension point
     (naming what you provide is a promise). It may never name a term some INSTANCE invented,
     because that term's home is the document the host can change.
  3. **Attribution that can fail.** Two hosts differ; each difference must contain something the
     host was TOLD -- a value in its measured reading, or in its own answer, or in the declaration
     of something it chose. An attribution that admits everything certifies rather than measures,
     so the placeholder is never a wildcard: a value is matched WHOLE, and a value the framework
     merely derived from a fact is not a value the host was told.
"""

from __future__ import annotations

import copy
import importlib
import itertools
import json
import re
import sys
from pathlib import Path

from harness import KIT, applied

MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
#: The rows live beside this suite, NOT in the kit: they are the kit-AUTHORING repository's
#: measurements of the kit, and a guard must name what it forbids -- so shipping it would hand every
#: host the very names it exists to keep out (owner's rule, 2026-09-13: the framework carries no
#: brand and no project identity). The shipped kit keeps the GRAMMAR (the registered schema).
DECLARATION = json.loads((Path(__file__).resolve().parent / "boundary.json").read_text(encoding="utf-8"))
#: The schema is found through the kit's own registry, by the declaration's own id. A second way
#: of knowing which schema governs this document would be a second home for that truth.
SCHEMA = json.loads(
    (KIT / MANIFEST["schemas"][DECLARATION["id"]]).read_text(encoding="utf-8"))

INTERPRETERS = KIT / "interpreters"
#: The install mode whose files are written once and owned by the host forever after. Schema
#: vocabulary, not a name this module invented: the capability schema declares the modes, and a
#: reader of a declaration may spell what the contract declares.
SEEDED = "seed"

for _extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir()
                                     if p.is_dir() and not p.name.startswith("_"))]:
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))


class BoundaryError(Exception):
    """A rule points at a scope its kind cannot read, or names a kind nobody provides. Refused
    rather than skipped: a rule that silently measures nothing reads exactly like a rule that
    looked and found nothing."""


def rules(where: str = None) -> list:
    return [rule for rule in DECLARATION["rules"]
            if where is None or where in rule["where"]]


# == the vocabulary a machine may and may not spell ===========================================
#: A TERM is a single slug-like token -- something that was named. Prose is not a term, a path is
#: not a term, and a version is not a term; none of them can be spelled in a machine by accident.
TERM = re.compile(r"^[a-z][a-z0-9]*([._-][a-z0-9]+)*$")


def _walk(node, keys: set, values: set) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(key)
            _walk(value, keys, values)
    elif isinstance(node, list):
        for value in node:
            _walk(value, keys, values)
    elif isinstance(node, str):
        values.add(node)


def _read_all(paths) -> tuple:
    keys, values = set(), set()
    for path in paths:
        _walk(json.loads(path.read_text(encoding="utf-8")), keys, values)
    return keys, values


def schema_terms() -> set:
    """What the CONTRACT declares. A schema is the one document both a declaration and its reader
    are entitled to know, so a term it carries is legitimately spelled on both sides."""
    keys, values = _read_all(sorted((KIT / "schemas").glob("*.json")))
    return {term for term in keys | values if TERM.match(term)}


def instance_terms() -> set:
    """What some INSTANCE invented. Harvested from every declaration in the kit that is not a
    schema -- values only, because a key is shape and a value is a name somebody chose."""
    #: The kit's own lockfile is excluded, and the reason is not convenience. This harvest asks
    #: *what did some INSTANCE invent* -- a term whose home is a document a host can change. A
    #: lockfile is the opposite: a READING the interpreter took of the kit, whose every value is
    #: either a digest or a word the machine itself provided. Harvesting it would invert the rule
    #: -- machine output re-entering as host vocabulary -- and, worse, it would make this sensor
    #: NONDETERMINISTIC: a digest beginning with a letter is a well-formed term, so whether a rule
    #: fired would depend on a hash. Found through the manifest's own declaration of where the
    #: lock lives, never by spelling the filename here.
    lock = KIT / MANIFEST["ships"]["lock"]
    documents = [path for path in sorted(KIT.rglob("*.json"))
                 if path.parent != KIT / "schemas" and path != lock]
    _keys, values = _read_all(documents)
    return {term for term in values if TERM.match(term)}


def interpreter_modules() -> list:
    found = []
    for path in sorted(INTERPRETERS.rglob("*.py")):
        found.append(importlib.import_module(path.stem))
    return found


def _carries_behaviour(value) -> bool:
    if callable(value):
        return True
    return isinstance(value, (tuple, list)) and any(callable(item) for item in value)


def provided_terms() -> set:
    """What a machine PROVIDES: the keys of its REGISTRIES -- an upper-case mapping that binds
    names to behaviour. That is exactly an extension point, and naming your own extension point is
    a promise, not a policy: a new row there is a new capability of the machine, not a new opinion
    about a domain. Provision is a property of the mapping and not of each row, so a registry with
    one behaviourless row still provides all its names. A mapping of pure data does not qualify,
    which is what keeps this from becoming a place to launder a domain word into the machine.

    This is also, precisely, where the ledger's open question lives: the install modes arrive here
    legitimately, and they remain the closest thing to policy inside the interpreter."""
    provided = set()
    for module in interpreter_modules() + [sys.modules[__name__]]:
        for name, value in vars(module).items():
            if name.isupper() and isinstance(value, dict) and value:
                if any(_carries_behaviour(item) for item in value.values()):
                    provided |= {key for key in value if isinstance(key, str)}
    return provided


def consumed_terms() -> set:
    """The terms no interpreter may spell: invented by an instance, promised by no contract, and
    provided by nobody. Computed once -- it walks every declaration and imports every module."""
    if not hasattr(consumed_terms, "_answer"):
        consumed_terms._answer = instance_terms() - schema_terms() - provided_terms()
    return consumed_terms._answer


# == the material the rules are pointed at =====================================================
class Surface:
    """One host's L6 surface: exactly the paths a run REPORTED writing, read back. Derived from
    the run and never from a list kept here -- a surface a test believes it knows is a second
    reading of something the kit already stated."""

    def __init__(self, root: Path, stdout: str) -> None:
        self.root = root
        self.paths = {}
        for _disposition, rel in applied(stdout):
            whole = root / rel
            if whole.is_file():
                self.paths[rel] = whole.read_text(encoding="utf-8")


class World:
    """Hosts, installed once per rule-set and reused. A `World` may be built over a FIXTURE kit,
    which is how a boundary sensor is shown a crossing without one ever being committed."""

    #: A host with nothing to say about itself: the subject of every scope that needs only one.
    AS_FOUND = {"id": "a-host-as-the-kit-finds-it", "material": {}}

    def __init__(self, fixtures, kit: Path = KIT) -> None:
        self.fixtures = fixtures
        self.kit = kit
        self._hosts = {}

    # -- scopes -------------------------------------------------------------------------------
    def interpreter_texts(self) -> list:
        return [(path.relative_to(self.kit).as_posix(), path.read_text(encoding="utf-8"))
                for path in sorted((self.kit / "interpreters").rglob("*.py"))]

    def emitted_texts(self) -> list:
        return sorted(self.surface(self.AS_FOUND).paths.items())

    def shipped_texts(self) -> list:
        """Every file the kit states it is made of -- enumerated from ITS lock, never walked off
        the disk -- as text. The kit core as a publisher hands it over, before any host, any
        adapter or any render has touched it (ADR-014)."""
        from harness import LOCK as _LOCK
        entries = json.loads((self.kit / _LOCK).read_text(encoding="utf-8"))["files"]
        return [(entry["path"], (self.kit / entry["path"]).read_text(encoding="utf-8", errors="replace"))
                for entry in sorted(entries, key=lambda e: e["path"])]

    def seeded_declarations(self) -> list:
        """Every seeded file that reached this host, beside the schema that governs it. A seed
        with no schema is yielded WITHOUT one rather than dropped: a file nobody can judge blank
        is a state, not an absence of one."""
        surface = self.surface(self.AS_FOUND)
        found = []
        for entry in MANIFEST["capabilities"]:
            declaration = json.loads(
                (self.kit / entry["declaration"]).read_text(encoding="utf-8"))
            for item in declaration["installs"]:
                if item["mode"] != SEEDED or item["target"] not in surface.paths:
                    continue
                try:
                    instance = json.loads(surface.paths[item["target"]])
                except ValueError:
                    continue  # prose, not a declaration -- the name rules read it instead
                schema = None
                if "validates" in item:
                    schema = json.loads(
                        (self.kit / MANIFEST["schemas"][item["validates"]]).read_text(
                            encoding="utf-8"))
                found.append((item["target"], instance, schema))
        return found

    def host_pairs(self, rule) -> list:
        return [(first, self.surface(first), second, self.surface(second))
                for first, second in itertools.combinations(rule["hosts"], 2)]

    # -- installation -------------------------------------------------------------------------
    def surface(self, spec: dict) -> Surface:
        if spec["id"] not in self._hosts:
            self._hosts[spec["id"]] = self._install(spec)
        return self._hosts[spec["id"]]

    def _install(self, spec: dict) -> Surface:
        host = self.fixtures.host()
        for rel, text in spec.get("material", {}).items():
            whole = host / rel
            whole.parent.mkdir(parents=True, exist_ok=True)
            whole.write_text(text, encoding="utf-8", newline="\n")
        flags = ("--enable", spec["enables"]) if "enables" in spec else ()
        drafted = self.fixtures.run_kit(self.kit, host, "init", *flags)
        assert drafted.returncode == 3, f"{spec['id']} did not stall at the door: {drafted.stderr}"
        approved = self.fixtures.run_kit(self.kit, host, "init", "--approve", "acceptance-suite")
        assert approved.returncode == 0, f"{spec['id']} did not install: {approved.stderr}"
        return Surface(host, approved.stdout)


# == the kinds -- one per WAY of measuring the boundary ========================================
class PatternRule:
    """A name in the open. The loud half of T1, and the whole of T2's second half: the same rows
    read the machinery and the blank it lays, because a name is no more welcome in what a host is
    handed than in what hands it."""

    ID = "absent-pattern"
    NEEDS = ("pattern",)

    @staticmethod
    def of_interpreters(world, rule) -> list:
        return world.interpreter_texts()

    @staticmethod
    def of_emitted(world, rule) -> list:
        return world.emitted_texts()

    @staticmethod
    def of_shipped(world, rule) -> list:
        return world.shipped_texts()

    @staticmethod
    def specimen(rule, which, world):
        return (f"<{rule['id']}:{which}>", rule[which])

    @staticmethod
    def findings(rule, subject) -> list:
        name, text = subject
        seen = sorted({match.group(0) for match in re.finditer(rule["pattern"], text)})
        return [f"{name}: {rule['id']} names {found!r} -- {rule['because']} "
                f"It belongs {rule['instead']}" for found in seen]


class InstanceTermRule:
    """The quiet half of T1. No pattern is declared and none could be: the vocabulary is HARVESTED
    from the declarations themselves, so it widens the moment a capability invents a word. That is
    the difference between this and a proper-noun grep -- one asks whether the machine said a name
    we thought of, the other asks whether it said a word that belongs to somebody else."""

    ID = "absent-instance-term"
    NEEDS = ()

    @staticmethod
    def of_interpreters(world, rule) -> list:
        return world.interpreter_texts()

    @staticmethod
    def specimen(rule, which, world):
        return (f"<{rule['id']}:{which}>", rule[which])

    @staticmethod
    def findings(rule, subject) -> list:
        name, text = subject
        found = []
        for term in sorted(consumed_terms()):
            if re.search(rf"""['"]{re.escape(term)}['"]""", text):
                found.append(f"{name}: {rule['id']} spells {term!r}, which only a declaration "
                             f"invented -- {rule['because']} It belongs {rule['instead']}")
        return found


class SeedRule:
    """T2. A seed is written once and owned by the host forever after, so a row in one is an
    answer the host will never be asked to give. Structure is what the SCHEMA declares; a row is
    what the schema leaves to whoever will live with it -- which is why the schema, not a list
    kept here, decides what counts as content."""

    ID = "empty-seeded-declaration"
    NEEDS = ()

    @staticmethod
    def of_emitted(world, rule) -> list:
        return world.seeded_declarations()

    @staticmethod
    def specimen(rule, which, world):
        return (f"<{rule['id']}:{which}>", rule[which]["instance"], rule[which]["schema"])

    @staticmethod
    def findings(rule, subject) -> list:
        name, instance, schema = subject
        if schema is None:
            return [f"{name}: {rule['id']} -- a seeded declaration that names no schema cannot be "
                    f"judged blank, and an unjudged file is not a blank one."]
        return [f"{name}: {rule['id']} arrives holding {row} -- {rule['because']} "
                f"It belongs {rule['instead']}" for row in SeedRule._rows(instance, schema, "")]

    @staticmethod
    def _rows(value, schema, path: str) -> list:
        rows = []
        if isinstance(value, list):
            rows += [f"{path}[{index}]" for index in range(len(value))]
        elif isinstance(value, dict):
            declared = (schema or {}).get("properties")
            if declared is None:
                rows += [f"{path}.{key}" for key in sorted(value)]
            else:
                for key, held in sorted(value.items()):
                    rows += SeedRule._rows(held, declared.get(key), f"{path}.{key}")
        return rows


class AttributionRule:
    """T3, the decisive one. Two hosts are installed and their surfaces compared; every line that
    appears in one and not the other must carry something that host was TOLD.

    What a host was told is not a vague set. It is: every name and every value in the documents
    the rule declares as ancestors, plus -- for the ancestor that records what the host CHOSE --
    the declarations of the chosen, because a choice carries its consequences in with it. And the
    match is WHOLE: a value the framework derived from a fact is not a value the host stated, so a
    basename cut out of a declared path attributes nothing. That is the line between adapting to a
    host and knowing something about it that it never said."""

    ID = "attributed-difference"
    NEEDS = ("ancestors", "hosts")

    @staticmethod
    def of_two_hosts(world, rule) -> list:
        return world.host_pairs(rule)

    @staticmethod
    def specimen(rule, which, world):
        """The two real surfaces, each additionally saying one thing the declaration names: a
        value the host stated whole, or a fragment the framework cut out of one. The specimen is
        presented TO the sensor rather than produced by a rigged kit, because the kit cannot
        currently be made to leak from a payload -- and a calibration that needs the subject to
        misbehave first is a calibration that never runs on a healthy system.

        The pair is the whole point. Both lines vary by host and only one of them is traceable, so
        this measures the EDGE: a sensor that flags both would refuse every honest adaptation, and
        a sensor that admits both would certify a leak."""
        first_spec, first, second_spec, second = world.host_pairs(rule)[0]
        emit = EMITTED_VALUES[rule[which]["emits"]]
        shared = sorted(set(first.paths) & set(second.paths))[0]
        return (first_spec, _also_saying(first, shared, emit(first)),
                second_spec, _also_saying(second, shared, emit(second)))

    @staticmethod
    def findings(rule, subject) -> list:
        first_spec, first, second_spec, second = subject
        #: What each host was told, judged against ITSELF. Demanding that the ancestor be told to
        #: this host ALONE reads stronger and is not: two installs a second apart share a moment,
        #: and the surface would then report a leak because two clocks agreed. The ADR's test is
        #: that a difference HAS an ancestor, not that it has an exclusive one.
        told_first = AttributionRule._told(rule, first)
        told_second = AttributionRule._told(rule, second)

        failures = []

        def judge(what: str, where: str, told: set, spec: dict) -> None:
            if not any(value in what for value in told):
                failures.append(
                    f"{spec['id']}:{where} -- {what.strip()!r} appears in this host and not in the "
                    f"other, and carries nothing this host was told. {rule['because']} "
                    f"It belongs {rule['instead']}")

        for rel in sorted(set(first.paths) ^ set(second.paths)):
            if rel in first.paths:
                judge(rel, "a path", told_first, first_spec)
            else:
                judge(rel, "a path", told_second, second_spec)

        for rel in sorted(set(first.paths) & set(second.paths)):
            here = AttributionRule._said(first.paths[rel])
            there = AttributionRule._said(second.paths[rel])
            for saying in sorted(here - there):
                judge(saying, rel, told_first, first_spec)
            for saying in sorted(there - here):
                judge(saying, rel, told_second, second_spec)
        return failures

    @staticmethod
    def _said(text: str) -> set:
        """What a file SAYS, read in its own language. A declaration is compared as the values it
        carries and never as the lines it is printed on: a list that lost an element moves a comma
        onto a different line, and a comparison that cannot tell that from a changed value spends
        its life reporting punctuation. An array's index is dropped for the same reason -- the
        third of four is the second of two, and neither host said anything different by it."""
        try:
            document = json.loads(text)
        except ValueError:
            return set(text.splitlines())
        said = set()
        _flatten(document, "", said)
        return said

    @staticmethod
    def _told(rule, surface: Surface) -> set:
        told = set()
        for ancestor in rule["ancestors"]:
            document = json.loads(
                (surface.root / ancestor["document"]).read_text(encoding="utf-8"))
            _spoken(document, told)
            for chosen in document.get(ancestor.get("chooses", ""), []):
                _spoken(_declaration_of(chosen), told)
        #: Two characters attribute anything. A value that short is not a name a host gave; it is
        #: a coincidence waiting to certify a leak.
        return {value for value in told if len(value) >= 3}


def _flatten(node, path: str, out: set) -> None:
    """Every scalar a document carries, under the route that reaches it."""
    if isinstance(node, dict):
        for key, value in sorted(node.items()):
            _flatten(value, f"{path}/{key}", out)
    elif isinstance(node, list):
        for value in node:
            _flatten(value, f"{path}[]", out)
    else:
        out.add(f"{path} = {json.dumps(node)}")


def _spoken(node, out: set) -> None:
    """Every name and every value in a document -- keys included, because the NAME of a measured
    fact is as much a thing the host was told as its value. Numbers are excluded deliberately: a
    number is not a name, and admitting one would let any line carrying a digit attribute itself."""
    if isinstance(node, dict):
        for key, value in node.items():
            out.add(key)
            _spoken(value, out)
    elif isinstance(node, list):
        for value in node:
            _spoken(value, out)
    elif isinstance(node, bool):
        out.add("true" if node else "false")
    elif isinstance(node, str):
        out.add(node)


def _declaration_of(capability_id: str) -> dict:
    entry = next(e for e in MANIFEST["capabilities"] if e["id"] == capability_id)
    return json.loads((KIT / entry["declaration"]).read_text(encoding="utf-8"))


def _also_saying(surface: Surface, rel: str, value: str) -> Surface:
    """The same surface, saying one more thing. Nothing is written: a calibration that had to
    corrupt a host in order to run would be a sensor that damages what it measures."""
    twin = copy.copy(surface)
    twin.paths = dict(surface.paths)
    twin.paths[rel] = surface.paths[rel] + f"\nthis host is {value}\n"
    return twin


#: The values a two-host specimen may be built from -- one the host stated whole, one the
#: framework cut out of what the host stated. The difference between them IS the boundary, which
#: is why they are the calibration and not an illustration of it.
EMITTED_VALUES = {
    "a-path-the-host-stated-whole": lambda surface: surface.root.as_posix(),
    "a-basename-cut-out-of-a-stated-path": lambda surface: surface.root.name,
}


#: One entry per WAY of measuring the boundary. A new way is a class and a row; the tests that
#: drive this file never learn its name.
KINDS = {kind.ID: kind for kind in (PatternRule, InstanceTermRule, SeedRule, AttributionRule)}


def _reader(scope: str, method: str):
    def read(kind, rule, world):
        found = getattr(kind, method, None)
        if found is None:
            raise BoundaryError(
                f"rule {rule['id']!r} is pointed at the scope {scope!r}, which its kind "
                f"{kind.ID!r} cannot read. A rule that measures nothing reads exactly like a "
                f"rule that looked and found nothing.")
        return found(world, rule)
    return read


#: The scopes a rule may be pointed at. Declared here, named in the declaration, and resolved by
#: kind -- one scope can mean two different subjects to two different sensors, which is why the
#: kind does the reading and this only says where.
SCOPES = {
    "interpreters": _reader("interpreters", "of_interpreters"),
    "emitted": _reader("emitted", "of_emitted"),
    "two-hosts": _reader("two-hosts", "of_two_hosts"),
    "shipped": _reader("shipped", "of_shipped"),
}


def kind_of(rule):
    if rule["kind"] not in KINDS:
        raise BoundaryError(
            f"rule {rule['id']!r} declares the kind {rule['kind']!r}, which nothing provides; "
            f"the provided kinds are {sorted(KINDS)}")
    return KINDS[rule["kind"]]


def calibration_failures(rule, world) -> list:
    """What a rule can prove about itself, before it is pointed at anything."""
    kind = kind_of(rule)
    missing = [need for need in kind.NEEDS if need not in rule]
    if missing:
        return [f"{rule['id']}: UNCALIBRATED -- its kind {kind.ID!r} reads {missing}, which this "
                f"rule does not declare, so it was never able to measure anything."]
    for scope in rule["where"]:
        if scope not in SCOPES:
            return [f"{rule['id']}: UNCALIBRATED -- it is pointed at {scope!r}, which is no "
                    f"declared scope; the declared scopes are {sorted(SCOPES)}."]

    failures = []
    blind = kind.findings(rule, kind.specimen(rule, "proves", world))
    if not blind:
        failures.append(
            f"{rule['id']}: UNCALIBRATED -- it does not see the specimen it declares it catches. "
            f"A sensor that cannot prove what it sees is not evidence, and nothing was scanned "
            f"on its word.")
    tolerated = kind.findings(rule, kind.specimen(rule, "admits", world))
    if tolerated:
        failures.append(
            f"{rule['id']}: UNCALIBRATED -- it also names the lookalike it declares legitimate: "
            f"{tolerated}. A rule with no measured edge eventually names everything, and nothing "
            f"was scanned on its word.")
    return failures


def scan(where: str, world) -> list:
    """Every rule declared for one scope, applied to it -- after every one of them has proved
    itself. An uncalibrated rule stops the scan: the tree is not read on the word of an unmeasured
    sensor, and the rule is itself the finding."""
    declared = rules(where)
    if not declared:
        raise BoundaryError(f"no rule is declared for the scope {where!r}, so this test measures "
                            f"nothing; a scope nobody points at is not a passing scope")
    uncalibrated = [failure for rule in declared
                    for failure in calibration_failures(rule, world)]
    if uncalibrated:
        return uncalibrated
    found = []
    for rule in declared:
        kind = kind_of(rule)
        for subject in SCOPES[where](kind, rule, world):
            found += kind.findings(rule, subject)
    return found
