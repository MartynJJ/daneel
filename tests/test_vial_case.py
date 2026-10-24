"""Tests for the screw-top vial case."""

import pytest

cq = pytest.importorskip("cadquery")

from daneel.parts.vial_case import VialCaseParams, build  # noqa: E402


@pytest.fixture(scope="module")
def case():
    p = VialCaseParams()
    body = build(VialCaseParams(piece="body")).val()
    lid = build(VialCaseParams(piece="lid")).val()
    return p, body, lid


def _slugs(p, extra=0.0):
    for x, y in p.centres():
        yield (
            cq.Workplane("XY")
            .workplane(offset=2.0)
            .center(x, y)
            .circle(p.vial_d / 2 + extra)
            .extrude(p.vial_h)
            .val()
        )


def test_validation():
    with pytest.raises(ValueError, match="count"):
        VialCaseParams(count=9).validate()
    with pytest.raises(ValueError, match="pocket_depth"):
        VialCaseParams(pocket_depth=40.0).validate()
    with pytest.raises(ValueError, match="piece"):
        VialCaseParams(piece="x").validate()


def test_four_vials_make_a_square_and_size_the_jar():
    p = VialCaseParams()
    xs = sorted({round(abs(x), 3) for x, _ in p.centres()})
    assert len(xs) == 1 and len(p.centres()) == 4
    assert p.outer_d() > 2 * (xs[0] * 2**0.5 + p.vial_d / 2)


def test_pieces_valid(case):
    _, body, lid = case
    assert body.isValid() and lid.isValid()
    assert len(build(VialCaseParams()).solids().vals()) == 2


def test_vials_fit_pockets_and_oversize_does_not(case):
    p, body, _ = case
    assert sum(body.intersect(s, tol=1e-4).Volume() for s in _slugs(p)) == pytest.approx(
        0, abs=0.01
    )
    assert sum(body.intersect(s, tol=1e-4).Volume() for s in _slugs(p, extra=0.7)) > 100


def test_vials_clear_the_lid(case):
    p, _, lid = case
    seated = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.height() + 2.5 + 0.3))
    assert sum(seated.intersect(s, tol=1e-4).Volume() for s in _slugs(p)) == pytest.approx(
        0, abs=0.01
    )
