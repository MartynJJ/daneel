"""Tests for the light-clip helmet mount."""

import pytest

from daneel.parts.light_mount import LightMountParams, build


def _solid(**kw):
    return build(LightMountParams(**kw)).val()


def test_default_is_valid_single_solid():
    s = _solid()
    bb = s.BoundingBox()
    assert s.isValid() and len(s.Solids()) == 1
    assert bb.zlen == pytest.approx(1.6 + 3.0 + 0.8, abs=0.05)


def test_block_width_follows_slot_and_clearance():
    narrow = _solid(slot_w=10.0, clearance=0.25).Volume()
    wide = _solid(slot_w=12.0, clearance=0.25).Volume()
    assert wide > narrow


def test_test_strip_has_three_blocks():
    s = _solid(piece="test")
    assert s.isValid() and len(s.Solids()) == 1
    assert s.Volume() > _solid().Volume()


def test_curved_underside_removes_material():
    flat = _solid(plate_t=4.0).Volume()
    curved = _solid(plate_t=4.0, helmet_radius=110.0).Volume()
    assert curved < flat


@pytest.mark.parametrize(
    "kw",
    [
        {"piece": "bad"},
        {"clearance": 1.0},
        {"bump_h": 3.0},
        {"plate_t": 1.0},
        {"helmet_radius": 30.0},
        {"helmet_radius": 110.0},
    ],
)
def test_rejects_bad_params(kw):
    with pytest.raises(ValueError):
        build(LightMountParams(**kw))
