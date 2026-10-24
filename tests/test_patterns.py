"""Tests for wall/lid patterns and engraved text on the jar and vial case."""

import pytest

cq = pytest.importorskip("cadquery")

from daneel.parts.jar import JarParams, build  # noqa: E402
from daneel.parts.patterns import FACE_PATTERNS, WALL_PATTERNS  # noqa: E402
from daneel.parts.vial_case import VialCaseParams  # noqa: E402
from daneel.parts.vial_case import build as build_case  # noqa: E402


@pytest.fixture(scope="module")
def plain():
    return (
        build(JarParams(piece="body")).val(),
        build(JarParams(piece="lid")).val(),
    )


def test_validation():
    with pytest.raises(ValueError, match="pattern must be"):
        JarParams(pattern="zigzag").validate()
    with pytest.raises(ValueError, match="lid_pattern must be"):
        JarParams(lid_pattern="flutes").validate()
    with pytest.raises(ValueError, match="under 2 mm"):
        JarParams(pattern="hex", pattern_depth=1.2).validate()
    with pytest.raises(ValueError, match="lid_top"):
        JarParams(lid_pattern="hex", lid_top=2.0).validate()


@pytest.mark.parametrize("kind", [k for k in WALL_PATTERNS if k != "none"])
def test_wall_pattern_cuts_only_below_the_shoulder(plain, kind):
    p = JarParams()
    body = build(JarParams(piece="body", pattern=kind)).val()
    assert body.isValid()
    assert plain[0].Volume() - body.Volume() > 100
    neck = (
        cq.Workplane("XY")
        .workplane(offset=p.height - p.thread_height)
        .rect(100, 100)
        .extrude(20)
        .val()
    )
    assert body.intersect(neck, tol=1e-4).Volume() == pytest.approx(
        plain[0].intersect(neck, tol=1e-4).Volume(), abs=0.5
    )


@pytest.mark.parametrize("kind", [k for k in FACE_PATTERNS if k != "none"])
def test_lid_pattern_cuts_the_top(plain, kind):
    lid = build(JarParams(piece="lid", lid_pattern=kind)).val()
    assert lid.isValid()
    assert plain[1].Volume() - lid.Volume() > 50


def test_patterned_lid_still_screws_on():
    p = JarParams()
    body = build(JarParams(piece="body", pattern="hex")).val()
    lid = build(JarParams(piece="lid", lid_pattern="hex", lid_text="BPC")).val()
    seated = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.height + p.lid_top + 0.3))
    for deg in (0, 90, 200):
        moved = seated.rotate((0, 0, 0), (0, 0, 1), deg).translate(
            (0, 0, deg / 360 * p.thread_pitch)
        )
        assert body.intersect(moved, tol=1e-4).Volume() == pytest.approx(0, abs=0.01)


def test_lid_text_is_mirrored_for_reading_from_outside(plain):
    lid = build(JarParams(piece="lid", lid_text="L", text_size=12.0)).val()
    removed = plain[1].cut(lid)
    assert removed.Volume() > 5
    # An "L" has its stem on the left; seen from underneath on the bed it is flipped to the right.
    assert removed.Center().x > 0.5


def test_vial_case_takes_patterns():
    case = build_case(VialCaseParams(piece="body", pattern="diamond"))
    assert case.val().isValid()
    VialCaseParams(lid_pattern="rays", lid_text="B-1").validate()
