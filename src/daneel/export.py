"""Export CadQuery geometry to disk. Format inferred from the file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_EXPORTERS = {".stl", ".step", ".stp", ".3mf"}


def export(model: Any, out: str | Path) -> Path:
    """Write `model` (a CadQuery Workplane) to `out`, creating parent dirs.

    CadQuery is imported lazily so that spec parsing / listing does not require
    the OpenCascade kernel.
    """
    path = Path(out)
    ext = path.suffix.lower()
    if ext not in _EXPORTERS:
        raise ValueError(f"unsupported export format {ext!r}; use one of {sorted(_EXPORTERS)}")
    import cadquery as cq

    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(path))
    return path
