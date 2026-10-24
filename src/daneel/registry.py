"""Part registry: map a part name to its params dataclass and `build` function.

Parts are imported lazily so that merely listing them does not pull in CadQuery.
Register a new part by adding one line to `_PARTS`.
"""

from __future__ import annotations

import importlib
from typing import Callable

# name -> (module, params-class name, build-fn name)
_PARTS: dict[str, tuple[str, str, str]] = {
    "card": ("daneel.parts.card", "CardParams", "build"),
    "box": ("daneel.parts.box", "BoxParams", "build"),
    "bracket": ("daneel.parts.bracket", "BracketParams", "build"),
    "calib_cube": ("daneel.parts.calib_cube", "CalibCubeParams", "build"),
    "jar": ("daneel.parts.jar", "JarParams", "build"),
}


def available() -> list[str]:
    """Sorted list of registered part names."""
    return sorted(_PARTS)


def get(name: str) -> tuple[type, Callable]:
    """Return (params_class, build_fn) for `name`. Imports the part module on demand."""
    if name not in _PARTS:
        raise KeyError(f"unknown part {name!r}; available: {', '.join(available())}")
    module_name, params_name, build_name = _PARTS[name]
    module = importlib.import_module(module_name)
    return getattr(module, params_name), getattr(module, build_name)


def companions(name: str):
    """Return the part module's optional ``companions(params, out_path)`` writer, or None.

    A part uses this to emit extra files beside its STL (e.g. calib_cube's marker sheet).
    """
    if name not in _PARTS:
        raise KeyError(f"unknown part {name!r}; available: {', '.join(available())}")
    module = importlib.import_module(_PARTS[name][0])
    return getattr(module, "companions", None)
