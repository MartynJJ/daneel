"""Tests for the calibration cube part and its marker sheet.

Param validation is CadQuery-free; geometry and marker tests skip when their
optional kernels/deps are absent (so CI without OpenCascade / OpenCV stays green).
"""

import pytest

from daneel.parts.calib_cube import FACES, CalibCubeParams


def test_pocket_side():
    assert CalibCubeParams(size=40, pocket_margin=4).pocket_side == 32


@pytest.mark.parametrize(
    "kw",
    [
        {"size": 0},
        {"pocket_margin": 25},  # 2*margin >= size
        {"recess_depth": 0},
        {"recess_depth": 30},  # >= size/2
        {"origin_chamfer": 4},  # >= pocket_margin
    ],
)
def test_validate_rejects(kw):
    with pytest.raises(ValueError):
        CalibCubeParams(**kw).validate()


def test_validate_accepts_default():
    CalibCubeParams().validate()  # no raise


def test_build_geometry():
    pytest.importorskip("cadquery")
    from daneel.parts.calib_cube import build

    p = CalibCubeParams(size=40)
    solid = build(p).val()
    assert solid.isValid()
    bb = solid.BoundingBox()
    # cube edge preserved (chamfer only nicks one corner)
    assert bb.xlen == pytest.approx(40, abs=0.01)
    assert bb.zlen == pytest.approx(40, abs=0.01)
    # sits on the bed
    assert bb.zmin == pytest.approx(0, abs=0.01)
    # five pockets + a chamfer removed material from the solid cube
    assert solid.Volume() < 40**3


def test_marker_sheet(tmp_path):
    pytest.importorskip("cv2")
    from daneel.parts import markers

    out = markers.write_marker_sheet(CalibCubeParams(size=40), tmp_path / "sheet.svg")
    svg = out.read_text()
    assert svg.startswith("<svg")
    assert 'width="210.0mm"' in svg  # A4
    assert svg.count("<text") >= len(FACES)  # one label per face + header
    assert "#000" in svg  # black marker cells rendered
