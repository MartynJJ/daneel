"""Tests for the heat-set insert coupon."""

import pytest

from daneel.parts.insert_coupon import InsertCouponParams, build


def test_default_valid_single_solid():
    s = build().val()
    assert s.isValid() and len(s.Solids()) == 1


def test_holes_remove_material():
    with_holes = build(InsertCouponParams(label=False)).val().Volume()
    bb = build(InsertCouponParams(label=False)).val().BoundingBox()
    assert with_holes < bb.xlen * bb.ylen * bb.zlen * 0.9


def test_diameters_centred_on_guess():
    assert InsertCouponParams().diameters("M3") == [4.0, 4.2, 4.4]


def test_bad_size_rejected():
    with pytest.raises(ValueError):
        build(InsertCouponParams(sizes=("M7",)))
