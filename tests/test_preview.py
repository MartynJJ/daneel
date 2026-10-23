"""Tests for the pre-flight preview (pure parsing; no slicer needed)."""

import json
import re
import zipfile

import pytest

from daneel import preview

GCODE = """\
G1 X10 Y10 E5
M83
; Z_HEIGHT: 0.2
G1 X20 Y10 F3000
G1 X30 Y10 E.5
G1 X30 Y20 E.5
G1 X30 Y20 E-.8
G0 X0 Y0
; Z_HEIGHT: 0.4
G1 X10 Y0 E.5
; Z_HEIGHT: 0.6
G1 Z0.8
"""


def test_extract_skips_start_travel_and_retracts():
    layers = preview.extract_layers(GCODE)
    assert [layer["z"] for layer in layers] == [0.2, 0.4]  # empty layer dropped
    assert layers[0]["segs"] == [[20.0, 10.0, 30.0, 10.0], [30.0, 10.0, 30.0, 20.0]]
    assert layers[1]["segs"] == [[0.0, 0.0, 10.0, 0.0]]


def test_build_data_centres_and_sizes():
    data = preview.build_data("p", preview.extract_layers(GCODE), 29.4, None)
    assert data["bbox"] == [30.0, 20.0] and data["z_height"] == 0.4
    assert data["est_min"] == 29 and data["layers"][0]["segs"][0][:2] == [5.0, 0.0]


def test_render_embeds_valid_json(tmp_path):
    data = preview.build_data("p</script>", preview.extract_layers(GCODE), None, 3.9)
    html = preview.render_html(data)
    assert "__DATA__" not in html and "</script>p" not in html
    blob = re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1)
    assert json.loads(blob.replace("<\\/", "</"))["grams"] == 3.9


def test_preview_3mf_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(preview, "read_3mf_estimates", lambda p: (17.0, 3.9))
    job = tmp_path / "cube.3mf"
    with zipfile.ZipFile(job, "w") as z:
        z.writestr("Metadata/plate_1.gcode", GCODE)
    page = preview.preview_3mf(job)
    assert page.name == "cube_preview.html" and "const DATA = {" in page.read_text()


def test_rejects_unsliced_3mf(tmp_path):
    job = tmp_path / "x.3mf"
    with zipfile.ZipFile(job, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
    with pytest.raises(preview.PreviewError):
        preview.preview_3mf(job)
