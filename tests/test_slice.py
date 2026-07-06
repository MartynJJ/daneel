"""Tests for the slicer interface (no real slicer binary required).

Validated against OrcaSlicer 2.4.1: command surface and the 3MF estimate format
(Metadata/slice_info.config with `prediction` seconds + filament `used_g`).
"""

import zipfile

import pytest

from daneel.config import SlicerConfig
from daneel.slice import SlicerError, SlicerInterface, read_3mf_estimates

_SLICE_INFO = """<?xml version="1.0"?>
<config>
  <plate>
    <metadata key="index" value="1"/>
    <metadata key="prediction" value="{prediction}"/>
    <filament id="1" type="PLA" used_m="2.30" used_g="{grams}"/>
  </plate>
</config>"""


def _make_3mf(path, prediction="1795", grams="12.34"):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Metadata/slice_info.config", _SLICE_INFO.format(prediction=prediction, grams=grams))
    return path


def test_build_command_includes_profiles_and_flags(tmp_path):
    cfg = SlicerConfig(
        binary="orca-slicer",
        machine_profile="/p/machine.json",
        process_profile="/p/process.json",
        filament_profile="/p/pla.json",
    )
    cmd = SlicerInterface(cfg).build_command(tmp_path / "in.stl", tmp_path / "out.3mf")
    assert cmd[0] == "orca-slicer"
    assert cmd[cmd.index("--load-settings") + 1] == "/p/machine.json;/p/process.json"
    assert cmd[cmd.index("--load-filaments") + 1] == "/p/pla.json"
    assert cmd[cmd.index("--slice") + 1] == "0"
    assert "--arrange" in cmd and "--export-3mf" in cmd
    assert cmd[-1] == str(tmp_path / "in.stl")


def test_build_command_requires_3mf(tmp_path):
    cfg = SlicerConfig(export_format="gcode")
    with pytest.raises(ValueError, match="3MF"):
        SlicerInterface(cfg).build_command(tmp_path / "in.stl", tmp_path / "out.gcode")


def test_dry_run_needs_no_binary_or_input(tmp_path):
    result = SlicerInterface(SlicerConfig()).slice(tmp_path / "nope.stl", dry_run=True)
    assert result.command[0] == "bambu-studio"
    assert result.output.suffix == ".3mf"


def test_resolve_binary_missing_raises():
    with pytest.raises(SlicerError):
        SlicerInterface(SlicerConfig(binary="definitely-not-a-real-slicer-xyz")).resolve_binary()


def test_slice_missing_input_raises(tmp_path):
    with pytest.raises(SlicerError, match="input model not found"):
        SlicerInterface(SlicerConfig(binary="sh")).slice(tmp_path / "missing.stl")


def test_read_3mf_estimates(tmp_path):
    path = _make_3mf(tmp_path / "m.3mf", prediction="1795", grams="12.34")
    duration, grams = read_3mf_estimates(path)
    assert duration == pytest.approx(29.9, abs=0.1)  # 1795 s
    assert grams == pytest.approx(12.34)


def test_read_3mf_estimates_zero_grams(tmp_path):
    # Filament profile without a density reports used_g=0 -> grams is None.
    path = _make_3mf(tmp_path / "m.3mf", prediction="600", grams="0.00")
    duration, grams = read_3mf_estimates(path)
    assert duration == pytest.approx(10.0)
    assert grams is None
