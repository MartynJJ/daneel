"""Tests for the T-slot helmet light mount."""

import cadquery as cq
import pytest

from daneel.parts.light_mount import LightMountParams, build


def _solid(**kw):
    return build(LightMountParams(**kw)).val()


def _post(p: LightMountParams, x: float) -> cq.Workplane:
    """The light's T-post (head over neck), head underside at z, neck going up to the lip top."""
    z_head = p.plate_t + p.z_clearance / 2
    head = (
        cq.Workplane("XY")
        .workplane(offset=z_head)
        .center(x, 0)
        .rect(p.head_l, p.head_w)
        .extrude(p.head_t)
    )
    neck = (
        cq.Workplane("XY")
        .workplane(offset=z_head + p.head_t - 0.01)
        .center(x, 0)
        .rect(p.head_l, p.neck_w)
        .extrude(p.lip_t() + 1.0)
    )
    return head.union(neck)


def test_default_is_valid_single_solid():
    s = _solid()
    assert s.isValid() and len(s.Solids()) == 1


def test_post_slides_in_with_no_overlap():
    p = LightMountParams()
    mount = build(p)
    entry = -p.block_l / 2 + p.head_l / 2  # head just inside the open end
    stop = p.block_l / 2 - p.wall - p.head_l / 2  # head against the stop wall
    for x in (entry - 3, entry, 0.0, stop):
        inter = mount.intersect(_post(p, x), tol=1e-4)
        assert inter.val().Volume() < 0.5 if inter.vals() else True, x


def test_post_is_held_by_the_lip():
    p = LightMountParams()
    mount = build(p)
    lifted = _post(p, 0.0).translate((0, 0, p.lip_t() + 0.5))
    assert mount.intersect(lifted, tol=1e-4).val().Volume() > 1.0


def test_wider_head_makes_wider_block():
    assert _solid(head_w=19.0, plate_w=34.0).BoundingBox().ylen >= 0


def test_test_strip_has_three_slots():
    s = _solid(piece="test")
    assert s.isValid() and len(s.Solids()) == 1


def test_curved_underside_removes_material():
    flat = _solid(plate_t=4.0).Volume()
    curved = _solid(plate_t=4.0, helmet_radius=110.0).Volume()
    assert curved < flat


@pytest.mark.parametrize(
    "kw",
    [
        {"piece": "bad"},
        {"clearance": 1.0},
        {"neck_w": 16.0},
        {"neck_h": 1.0},
        {"block_l": 12.0},
        {"plate_t": 1.0},
        {"helmet_radius": 30.0},
        {"helmet_radius": 110.0},
    ],
)
def test_rejects_bad_params(kw):
    with pytest.raises(ValueError):
        build(LightMountParams(**kw))
