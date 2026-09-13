"""Acceptance: the boundary -- ADR-001 point 2, made executable.

That ADR states where this framework stops: it owns the truth about the PROCESS by which a domain
is settled, never the decision itself. It then names three measurements, and until now all three
were sentences. A boundary described in prose is a boundary nobody can be shown to have crossed --
and this framework was built beside one particular repository, which is precisely the condition
under which the universal is indistinguishable from the familiar.

  * **T1, the name test** -- nothing in the machinery may name a project, a stack, a role or a
    runtime. Both halves: the proper noun, and the quieter one, a term some INSTANCE invented that
    ends up spelled in the machine, where it becomes a second home for a judgement the host thinks
    it owns.
  * **T2, the blank test** -- everything emitted must be valid and useful holding NOTHING about
    any domain. A seed arrives once and is owned by the host forever after, so a row inside one is
    an answer the host will never be asked to give.
  * **T3, the two-host test** -- the decisive one, because the first two can be satisfied by a
    framework that is merely careful. Install into two maximally different repositories and every
    difference must trace to something the framework was TOLD.

Nothing here restates the rules. They are READ from `tests/acceptance/fresh-repo/boundary.json` and this suite is
driven by them, and two of these tests exist only to prove that the sensors are pointed at
something: an attribution that cannot fail does not measure, it certifies.
"""

from __future__ import annotations

import unittest

import boundary
import validation
from harness import Fixtures


class Boundary(Fixtures, unittest.TestCase):

    _world = None

    @classmethod
    def world(cls):
        """One set of hosts for the whole suite. Installing is the expensive part and none of
        these tests writes to a host, so a second install would measure the same thing twice."""
        if cls._world is None:
            cls._world = boundary.World(cls)
        return cls._world

    # == 0. the sensor is measured before it is believed =======================================
    def test_70_every_boundary_rule_proves_what_it_sees_and_admits_what_it_tolerates(self):
        """The calibration is in the DECLARATION, and it covers every kind -- including the
        two-host one, whose specimen is a whole fixture kit that leaks and one that does not.
        A rule that cannot flag its own crossing and admit its own lookalike has no measured
        edge, and a rule with no edge eventually names everything."""
        self.assertEqual([], validation.validate(boundary.DECLARATION, boundary.SCHEMA),
                         "the boundary declaration does not honour its own schema")
        self.assertTrue(boundary.rules(), "a boundary that declares no rule gates nothing")
        for rule in boundary.rules():
            with self.subTest(rule=rule["id"]):
                self.assertEqual([], boundary.calibration_failures(rule, self.world()))

    # == 1. T1 -- the name test ================================================================
    def test_71_nothing_in_the_machinery_names_a_project_a_stack_a_role_or_a_runtime(self):
        """T1. The interpreters are scanned by every rule declared over them -- the proper-noun
        half and the invented-term half together, because a machine that names what it consumes
        has taken a side whether or not the word was capitalised."""
        self.assertEqual([], boundary.scan("interpreters", self.world()))

    def test_72_the_vocabulary_a_machine_may_spell_is_the_contract_and_what_it_provides(self):
        """The calibration T1's quiet half needs and cannot carry as a specimen: proof that the
        harvest is pointed at something. If the declarations yielded no invented term, or every
        one of them turned out to be contract vocabulary, the scan above would pass by looking at
        an empty set -- which reads exactly like a scan that found nothing."""
        invented = boundary.instance_terms()
        contract = boundary.schema_terms()
        provided = boundary.provided_terms()
        consumed = boundary.consumed_terms()

        self.assertTrue(invented, "no declaration in this kit invented a term, so nothing is measured")
        self.assertTrue(contract, "no schema declares a term, so every term would read as invented")
        self.assertTrue(provided, "no interpreter provides an extension point, which cannot be true")
        self.assertTrue(consumed, "every invented term turned out to be contract vocabulary; the "
                                  "scan above is then looking at an empty set")
        self.assertEqual(set(), consumed & contract)
        self.assertEqual(set(), consumed & provided)

    # == 2. T2 -- the blank test ===============================================================
    def test_73_nothing_emitted_into_a_fresh_host_says_anything_about_a_domain(self):
        """T2. Every rule declared over the emitted surface, applied to exactly the files a fresh
        install reported writing: a name in what a host is HANDED is no more welcome than a name
        in what hands it, and a seeded declaration that arrives holding rows has answered for the
        host in the one file no upgrade will ever revisit."""
        self.assertEqual([], boundary.scan("emitted", self.world()))

    def test_74_the_blank_test_actually_judged_the_seeds_this_kit_ships(self):
        """The calibration T2 needs. A seed the suite could not judge -- unparsed, or governed by
        no schema -- must not read as a blank one, so the count is asserted and the unjudgeable
        are named. A blank test that judged nothing is a certificate."""
        seeds = self.world().seeded_declarations()
        self.assertTrue(seeds, "this kit seeds nothing, so the blank test measures nothing")
        unjudgeable = [name for name, _instance, schema in seeds if schema is None]
        self.assertEqual([], unjudgeable,
                         "a seeded declaration governed by no schema cannot be judged blank")

    # == 3. T3 -- the two-host test ============================================================
    def test_75_the_two_declared_hosts_differ_in_every_declared_ancestor(self):
        """The calibration T3 needs, and the one it is easiest to skip. Two hosts that resemble
        each other produce no differences and the attribution passes gloriously, having measured
        nothing. So before any diff is read: every ancestor document exists in both hosts, and
        every one of them actually SAYS something different -- a reading that differs, and an
        answer that differs. If the framework ever stops adapting, this is what goes red."""
        for rule in boundary.rules("two-hosts"):
            for first_spec, first, second_spec, second in self.world().host_pairs(rule):
                for ancestor in rule["ancestors"]:
                    with self.subTest(rule=rule["id"], ancestor=ancestor["id"]):
                        here = first.paths.get(ancestor["document"])
                        there = second.paths.get(ancestor["document"])
                        self.assertIsNotNone(here, f"{first_spec['id']} never received it")
                        self.assertIsNotNone(there, f"{second_spec['id']} never received it")
                        self.assertNotEqual(
                            here, there,
                            "both hosts were told the same thing here, so any difference this "
                            "ancestor is credited with was not caused by it")

    def test_76_the_surface_being_compared_is_exactly_what_each_run_reported_writing(self):
        """The premise T3 stands on. The L6 surface is derived from what the kit SAID it wrote,
        never from a list this suite keeps -- a surface a test believes it knows is a second
        reading of something the kit already stated, and the two drift silently. Proved by the
        one thing that must never appear in it: the material the host had before the kit ran."""
        for rule in boundary.rules("two-hosts"):
            for spec, surface in [(s, self.world().surface(s)) for s in rule["hosts"]]:
                with self.subTest(host=spec["id"]):
                    self.assertTrue(surface.paths, "a host received nothing at all")
                    for rel in spec.get("material", {}):
                        self.assertNotIn(rel, surface.paths,
                                         "the kit claimed to have written what the host arrived "
                                         "with, so the surface is not what was reported")
                        self.assertTrue((surface.root / rel).is_file(),
                                        "the host's own file did not survive the install")

    def test_77_every_difference_between_two_maximally_different_hosts_has_an_ancestor(self):
        """T3, and ADR-001 calls it the only decisive one. Two repositories with nothing in common
        but a `.git` directory, and every line that appears in one surface and not the other must
        carry something that host was TOLD: a fact its profile measured, an answer it gave at the
        door, or a declaration it pulled in by choosing something. A difference with no ancestor is
        the framework speaking about a domain it was never given -- and it will read as adaptation
        right up until it is wrong somewhere it was never installed."""
        self.assertEqual([], boundary.scan("two-hosts", self.world()))
