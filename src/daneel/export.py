"""Export CadQuery geometry to disk. Format inferred from the file extension."""

from __future__ import annotations

from pathlib import Path

import cadquery as cq

_EXPORTERS = {".stl", ".step", ".stp", ".3mf"}


def export(model: cq.Workplane, out: str | Path) -> Path:
    """Write `model` to `out`, creating parent dirs. Returns the path written."""
    path = Path(out)
    ext = path.suffix.lower()
    if ext not in _EXPORTERS:
        raise ValueError(f"unsupported export format {ext!r}; use one of {sorted(_EXPORTERS)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(path))
    return path
