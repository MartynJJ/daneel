"""Tests for the screw-top jar (geometry + fit)."""

import math

import pytest

cq = pytest.importorskip("cadquery")

from daneel.parts.jar import JarParams, build  # noqa: E402


@pytest.fixture(scope="module")
def pieces():
    p = JarParams()
    body = build(JarParams(piece="body")).val()
    lid = build(JarParams(piece="lid")).val()
    seated = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.height + p.lid_top + 0.3))
    return p, body, lid, seated


def _overlap(body, lid):
    return body.intersect(lid, tol=1e-4).Volume()


def test_validation_rejects_thin_neck_and_fine_pitch():
    with pytest.raises(ValueError, match="neck wall"):
        JarParams(wall=2.0).validate()
    with pytest.raises(ValueError, match="pitch too fine"):
        JarParams(thread_pitch=2.0).validate()
    with pytest.raises(ValueError, match="piece"):
        JarParams(piece="nope").validate()


def test_pieces_are_valid_single_solids(pieces):
    _, body, lid, _ = pieces
    assert body.isValid() and lid.isValid()
    assert len(build(JarParams(piece="both")).vals()) == 2


def test_threads_actually_fused(pieces):
    p, body, _, _ = pieces
    r = p.outer_d / 2
    r_root = r - p.thread_depth
    r_in = r - p.wall
    shoulder = p.height - p.thread_height
    bare = (
        math.pi * (r**2 - r_in**2) * shoulder
        + math.pi * r_in**2 * p.floor
        + math.pi * (r_root**2 - r_in**2) * p.thread_height
    )
    assert body.Volume() > bare + 200

    plain = build(JarParams(piece="lid", grip=0)).val()
    depth = p.thread_height + 0.3
    no_ridge = (
        math.pi * (r + p.lid_wall) ** 2 * (p.lid_top + depth)
        - math.pi * (r + p.clearance) ** 2 * depth
    )
    assert plain.Volume() > no_ridge + 200


@pytest.mark.parametrize("deg", [0, 45, 150, 270])
def test_lid_screws_on_without_interference(pieces, deg):
    p, body, _, seated = pieces
    lift = deg / 360 * p.thread_pitch
    moved = seated.rotate((0, 0, 0), (0, 0, 1), deg).translate((0, 0, lift))
    assert _overlap(body, moved) == pytest.approx(0, abs=0.5)


@pytest.mark.parametrize("deg", [60, 120, 240])
def test_turning_without_lifting_collides(pieces, deg):
    _, body, _, seated = pieces
    moved = seated.rotate((0, 0, 0), (0, 0, 1), deg)
    assert _overlap(body, moved) > 5
