"""Tests for scan intake (skipped without the [scan] extra)."""

import pytest

trimesh = pytest.importorskip("trimesh")
pytest.importorskip("fast_simplification")

from daneel.scan import ScanError, prepare, scale_from_reference  # noqa: E402


def _write(tmp_path, mesh, name="scan.stl"):
    p = tmp_path / name
    mesh.export(str(p))
    return p


def test_scale_from_reference():
    assert scale_from_reference(20.0, 0.5) == 40.0
    with pytest.raises(ScanError):
        scale_from_reference(0, 1)


def test_scales_seats_on_bed_and_centres(tmp_path):
    box = trimesh.creation.box(extents=(1, 2, 3))
    box.apply_translation((10, -5, 7))  # arbitrary position
    src = _write(tmp_path, box)
    rep = prepare(src, tmp_path / "out.stl", scale=10.0)
    out = trimesh.load(str(tmp_path / "out.stl"))
    assert rep.extents_mm == pytest.approx((10, 20, 30))
    assert out.bounds[0] == pytest.approx([-5, -10, 0])
    assert rep.watertight


def test_fills_hole_and_drops_debris(tmp_path):
    sphere = trimesh.creation.icosphere(subdivisions=2, radius=5)
    keep = [i for i in range(len(sphere.faces)) if i not in (0, 1)]
    sphere.update_faces(keep)
    sphere.remove_unreferenced_vertices()
    assert not sphere.is_watertight
    debris = trimesh.creation.box(extents=(0.1, 0.1, 0.1))
    debris.apply_translation((50, 50, 50))
    src = _write(tmp_path, trimesh.util.concatenate([sphere, debris]))
    rep = prepare(src, tmp_path / "out.stl")
    assert rep.watertight
    assert any("fragment" in n for n in rep.notes)


def test_decimates(tmp_path):
    sphere = trimesh.creation.icosphere(subdivisions=4)
    src = _write(tmp_path, sphere)
    rep = prepare(src, tmp_path / "out.stl", max_faces=500)
    assert rep.faces_out <= 600 and rep.faces_in > 1000


def test_rejects_empty_and_bad_scale(tmp_path):
    p = tmp_path / "empty.stl"
    p.write_text("not a mesh")
    with pytest.raises(ScanError):
        prepare(p, tmp_path / "o.stl")
    box = _write(tmp_path, trimesh.creation.box())
    with pytest.raises(ScanError):
        prepare(box, tmp_path / "o.stl", scale=0)
