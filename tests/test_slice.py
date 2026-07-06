"""Tests for the slicer interface (no real slicer binary required)."""

import pytest

from daneel.config import SlicerConfig
from daneel.slice import SlicerError, SlicerInterface, parse_estimates


def test_build_command_includes_profiles_and_io(tmp_path):
    cfg = SlicerConfig(
        binary="orca-slicer",
        machine_profile="/p/machine.json",
        process_profile="/p/process.json",
        filament_profile="/p/pla.json",
        export_format="3mf",
    )
    cmd = SlicerInterface(cfg).build_command(tmp_path / "in.stl", tmp_path / "out.3mf")
    assert cmd[0] == "orca-slicer"
    assert "--load-settings" in cmd
    assert cmd[cmd.index("--load-settings") + 1] == "/p/machine.json;/p/process.json"
    assert cmd[cmd.index("--load-filaments") + 1] == "/p/pla.json"
    assert "--export-3mf" in cmd
    assert str(tmp_path / "in.stl") == cmd[-1]


def test_build_command_rejects_bad_format(tmp_path):
    cfg = SlicerConfig(export_format="obj")
    with pytest.raises(ValueError):
        SlicerInterface(cfg).build_command(tmp_path / "in.stl", tmp_path / "out.obj")


def test_dry_run_does_not_require_binary_or_input(tmp_path):
    result = SlicerInterface(SlicerConfig()).slice(tmp_path / "nope.stl", dry_run=True)
    assert result.command[0] == "bambu-studio"
    assert result.output.suffix == ".3mf"


def test_resolve_binary_missing_raises():
    iface = SlicerInterface(SlicerConfig(binary="definitely-not-a-real-slicer-xyz"))
    with pytest.raises(SlicerError):
        iface.resolve_binary()


def test_slice_missing_input_raises(tmp_path):
    # Use a real binary name so resolution isn't the failure; input is absent.
    iface = SlicerInterface(SlicerConfig(binary="sh"))
    with pytest.raises(SlicerError, match="input model not found"):
        iface.slice(tmp_path / "missing.stl")


def test_parse_estimates():
    text = "total estimated time: 1h 23m 45s\nfilament used [g] = 12.34\n"
    duration, grams = parse_estimates(text)
    assert duration == pytest.approx(83.75)
    assert grams == pytest.approx(12.34)


def test_parse_estimates_absent():
    assert parse_estimates("no numbers here") == (None, None)
