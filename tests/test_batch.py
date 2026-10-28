"""Tests for the CadQuery-free logic (registry, coercion, spec loading).

Geometry building requires the OpenCascade kernel and is not exercised here.
"""

from pathlib import Path

from daneel import batch, registry

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_registry_lists_stock_parts():
    assert registry.available() == [
        "box",
        "bracket",
        "calib_cube",
        "card",
        "enclosure",
        "hinge",
        "jar",
        "light_mount",
        "vial_case",
        "vial_holder",
    ]


def test_coerce_types():
    assert batch.coerce("bool", "yes") is True
    assert batch.coerce("bool", "false") is False
    assert batch.coerce("int", "12.0") == 12
    assert batch.coerce("float", "3.5") == 3.5
    assert batch.coerce("str", "hi") == "hi"


def test_load_csv_spec():
    rows = batch.load_spec(EXAMPLES / "batch.example.csv")
    assert rows[0]["part"] == "box"
    assert rows[1]["width"] == "80"


def test_load_yaml_spec():
    rows = batch.load_spec(EXAMPLES / "batch.example.yaml")
    assert rows[1]["part"] == "bracket"
    assert rows[2]["out"] == "tag-a17.stl"
