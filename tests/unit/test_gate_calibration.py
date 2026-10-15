"""Unit: a gate is trusted only after it bit (ADR-022 decision 8, slice S6).

Every calibration a gate module publishes is run against a host fixture it builds itself: its specimen
must be flagged and its lookalike admitted. A calibration for a kind nobody registers is an orphan and
fails. The kinds without one are counted by the published measure -- never listed here, because a list
kept in a test is a second home for a number the measure already states.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import calibration  # noqa: E402
import gatekinds  # noqa: E402
from manifest import Manifest  # noqa: E402
from workspace import Workspace  # noqa: E402

MANIFEST = Manifest(KIT)
_TRASH = []


def host(files: dict, **extra) -> types.SimpleNamespace:
    """A host holding exactly these files, with the real manifest and whatever else a kind reads."""
    root = Path(tempfile.mkdtemp(prefix="calibrate-"))
    _TRASH.append(root)
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    return types.SimpleNamespace(workspace=Workspace(root), manifest=MANIFEST, **extra)


def teardown_module():
    for root in _TRASH:
        shutil.rmtree(root, ignore_errors=True)


def test_every_calibrated_kind_flags_its_specimen_and_admits_its_lookalike():
    calibrations = gatekinds.registry("CALIBRATIONS")
    assert calibrations, "no gate kind publishes a calibration"
    for kind, calibrate in sorted(calibrations.items()):
        flagged, admitted = calibrate(host)
        assert flagged, f"{kind}: its specimen was not flagged -- the gate cannot bite"
        assert not admitted, f"{kind}: its lookalike was flagged -- the gate bites the innocent: {admitted}"


def test_no_calibration_is_an_orphan():
    orphans = sorted(set(gatekinds.registry("CALIBRATIONS")) - set(gatekinds.registry()))
    assert not orphans, f"calibrations for kinds no module registers: {orphans}"


def test_the_uncalibrated_kinds_are_published_as_a_measure_and_some_are_calibrated():
    assert calibration.UNCALIBRATED in calibration.MEASURES
    assert len(calibration.uncalibrated()) < len(gatekinds.registry()), "every kind is uncalibrated"
