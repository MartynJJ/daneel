"""Tests for the print-in-place hinge."""

import pytest

cq = pytest.importorskip("cadquery")

from daneel.parts.hinge import HingeParams, build  # noqa: E402


@pytest.fixture(scope="module")
def leaves():
    solids = build(HingeParams()).solids().vals()
    assert len(solids) == 2
    return solids


def _overlap(a, b):
    return a.intersect(b, tol=1e-4).Volume()


def test_validation():
    with pytest.raises(ValueError, match="odd"):
        HingeParams(knuckles=4).validate()
    with pytest.raises(ValueError, match="clearance"):
        HingeParams(clearance=0.05).validate()
    with pytest.raises(ValueError, match="axial_gap"):
        HingeParams(axial_gap=0.1).validate()


def test_leaves_are_separate_valid_solids(leaves):
    a, b = leaves
    assert a.isValid() and b.isValid()
    assert _overlap(a, b) == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("deg", [30, 90, 150, 180])
def test_leaf_swings_freely(leaves, deg):
    a, b = leaves
    r = HingeParams().barrel_d / 2
    assert _overlap(a, b.rotate((0, 0, r), (1, 0, r), deg)) == pytest.approx(0, abs=0.01)


def test_off_axis_rotation_collides(leaves):
    a, b = leaves
    r = HingeParams().barrel_d / 2
    assert _overlap(a, b.rotate((0, 0, r + 1.5), (1, 0, r + 1.5), 60)) > 1


def test_leaf_b_is_captive_between_a_knuckles(leaves):
    a, b = leaves
    assert _overlap(a, b.translate((HingeParams().axial_gap + 0.2, 0, 0))) > 0.5
