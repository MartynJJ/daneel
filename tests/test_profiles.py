"""Tests for preset flattening."""

import json

import pytest

from daneel.profiles import ProfileError, flatten


def _w(d, name, **kw):
    (d / f"{name}.json").write_text(json.dumps({"name": name, **kw}))


def test_child_overrides_parent_and_inherits_density(tmp_path):
    _w(tmp_path, "root", filament_density=["0"], filament_type=["PLA"])
    _w(tmp_path, "mid", inherits="root", filament_density=["1.24"], filament_cost=["20"])
    _w(tmp_path, "leaf", inherits="mid", nozzle_temperature=["220"])
    out = flatten(tmp_path / "leaf.json")
    assert out["filament_density"] == ["1.24"]
    assert out["nozzle_temperature"] == ["220"] and out["filament_cost"] == ["20"]
    assert "inherits" not in out and out["name"] == "leaf"


def test_missing_parent_and_loop(tmp_path):
    _w(tmp_path, "a", inherits="nope")
    with pytest.raises(ProfileError):
        flatten(tmp_path / "a.json")
    _w(tmp_path, "x", inherits="y")
    _w(tmp_path, "y", inherits="x")
    with pytest.raises(ProfileError):
        flatten(tmp_path / "x.json")
