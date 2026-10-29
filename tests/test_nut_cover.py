"""Tests for the hex nut cover."""

import math

import cadquery as cq
import pytest

from daneel.parts.nut_cover import NutCoverParams, build


def _solid(**kw):
    return build(NutCoverParams(**kw)).val()


def test_default_is_valid_single_solid():
    s = _solid()
    bb = s.BoundingBox()
    assert s.isValid() and len(s.Solids()) == 1
    assert bb.zlen == pytest.approx(20.6, abs=0.01) and bb.xlen == pytest.approx(35.0, abs=0.05)


def test_closed_end_is_on_the_bed():
    cap = build(NutCoverParams())
    roof = cap.intersect(cq.Workplane("XY").box(40, 40, 3.0, centered=(True, True, False)))
    p = NutCoverParams()
    expected = (p.outer_af**2 * math.sqrt(3) / 2) * 3.0
    assert roof.val().Volume() == pytest.approx(expected, rel=0.01)


def test_nut_fits_in_pocket():
    p = NutCoverParams()
    nut = (
        cq.Workplane("XY")
        .polygon(6, 21.0 / math.cos(math.radians(30)))
        .extrude(p.pocket_depth - 0.5)
        .translate((0, 0, p.height - p.pocket_depth))
    )
    inter = build(p).intersect(nut, tol=1e-4)
    assert not inter.vals() or inter.val().Volume() < 0.5


def test_flange_overhang_is_at_most_45_degrees():
    p = NutCoverParams()
    cone_rise = (p.flange_d - p.outer_af) / 2
    z0 = p.height - p.flange_t
    below = build(p).intersect(
        cq.Workplane("XY").box(60, 60, z0, centered=(True, True, False)), tol=1e-4
    )
    assert below.val().BoundingBox().xlen < p.outer_af / math.cos(math.radians(30)) + 0.1
    assert p.flange_t >= cone_rise + 1.5


def test_count_makes_separate_caps():
    assert len(_solid(count=3).Solids()) == 3


@pytest.mark.parametrize(
    "kw",
    [
        {"nut_af": 2.0},
        {"outer_af": 23.0},
        {"pocket_depth": 20.0},
        {"flange_d": 30.0},
        {"flange_t": 3.0},
        {"count": 9},
        {"gap": 1.0},
    ],
)
def test_rejects_bad_params(kw):
    with pytest.raises(ValueError):
        build(NutCoverParams(**kw))
