"""Flatten OrcaSlicer/Bambu Studio presets so the headless CLI sees inherited values.

System presets store only their deltas and name a parent in ``inherits``. The CLI
does not resolve that chain for ``--load-filaments``, so inherited values such as
``filament_density`` come through as the root default (0) and the slice reports 0 g.
:func:`flatten` merges the chain (child wins) into one self-contained JSON.
"""

from __future__ import annotations

import json
from pathlib import Path


class ProfileError(RuntimeError):
    pass


def flatten(path: str | Path) -> dict:
    """Resolve ``inherits`` for the preset at ``path``; parents are looked up beside it."""
    path = Path(path)
    chain: list[dict] = []
    seen: set[str] = set()
    current: Path | None = path
    while current is not None:
        if current.name in seen:
            raise ProfileError(f"inheritance loop at {current.name}")
        seen.add(current.name)
        if not current.exists():
            raise ProfileError(f"preset not found: {current}")
        data = json.loads(current.read_text())
        chain.append(data)
        parent = data.get("inherits")
        current = path.parent / f"{parent}.json" if parent else None

    merged: dict = {}
    for data in reversed(chain):  # root first, so children override
        merged.update(data)
    merged.pop("inherits", None)
    merged["name"] = path.stem
    return merged
