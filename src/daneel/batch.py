"""Batch generation: build many models from a CSV or YAML spec, with a manifest.

Each spec entry names a `part` (or relies on a default) plus any parameters to
override; unspecified parameters fall back to the part's defaults. An optional
`out` field sets the filename, otherwise names are `<part>_<index>.<fmt>`.

CSV — one row per model, header names match part parameters::

    part,length,width,height
    box,80,50,30
    box,120,80,40

YAML — a list, or a mapping with a `parts:` key::

    - part: box
      length: 80
    - part: bracket
      leg_a: 40
"""

from __future__ import annotations

import csv
import json
from dataclasses import fields
from pathlib import Path
from typing import Any

from daneel import registry
from daneel.export import export

_RESERVED = {"part", "out"}


def coerce(annotation: Any, value: Any) -> Any:
    """Coerce a spec string to the field's type. Handles string annotations
    (from `from __future__ import annotations`) and real types alike."""
    if isinstance(value, bool):
        return value
    name = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", "str")
    s = str(value).strip()
    if name == "bool":
        return s.lower() in {"1", "true", "yes", "y", "on"}
    if name == "int":
        return int(float(s))
    if name == "float":
        return float(s)
    return s


def params_from_mapping(part: str, mapping: dict[str, Any]) -> tuple[Any, Any]:
    """Build a params instance for `part` from a spec row. Returns (params, build_fn)."""
    params_cls, build = registry.get(part)
    field_types = {f.name: f.type for f in fields(params_cls)}
    kwargs: dict[str, Any] = {}
    for key, value in mapping.items():
        if key in _RESERVED or value in (None, ""):
            continue
        if key not in field_types:
            raise KeyError(f"part {part!r} has no parameter {key!r}")
        kwargs[key] = coerce(field_types[key], value)
    return params_cls(**kwargs), build


def load_spec(path: str | Path) -> list[dict[str, Any]]:
    """Read a CSV/YAML spec into a list of row mappings."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        with p.open(newline="") as fh:
            return list(csv.DictReader(fh))
    if ext in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(p.read_text())
        if isinstance(data, dict):
            data = data.get("parts", [])
        if not isinstance(data, list):
            raise ValueError("YAML spec must be a list or a mapping with a 'parts' list")
        return data
    raise ValueError(f"unsupported spec format {ext!r}; use .csv, .yaml or .yml")


def run(
    spec: str | Path,
    outdir: str | Path = "output",
    fmt: str = "stl",
    default_part: str | None = None,
) -> list[dict[str, Any]]:
    """Generate every model in `spec`, write files under `outdir`, and a manifest.

    Returns the manifest (also written to `<outdir>/manifest.json`).
    """
    rows = load_spec(spec)
    out_root = Path(outdir)
    out_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        part = row.get("part") or default_part
        if not part:
            raise ValueError(f"spec entry {i}: no 'part' given and no default_part set")
        params, build = params_from_mapping(part, row)
        filename = row.get("out") or f"{part}_{i:03d}.{fmt}"
        path = export(build(params), out_root / filename)
        manifest.append(
            {"index": i, "part": part, "output": str(path), "params": vars(params)}
        )

    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
