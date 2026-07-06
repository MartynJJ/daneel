"""Printer / slicer configuration.

Loads from (in priority order):
  1. explicit path passed to `load()`
  2. $DANEEL_CONFIG
  3. ~/.config/daneel/config.toml

Never commit real access codes — config.toml is git-ignored. See config.example.toml.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # py311+
    import tomllib
except ModuleNotFoundError:  # py310
    import tomli as tomllib  # type: ignore[no-redef]

from pydantic import BaseModel, Field


class PrinterConfig(BaseModel):
    """Bambu P1S LAN-mode connection details."""

    ip: str = Field(..., description="Printer LAN IP, e.g. 192.168.1.50")
    serial: str = Field(..., description="Printer serial number")
    access_code: str = Field(..., description="LAN access code from the printer screen")


class SlicerConfig(BaseModel):
    """Headless slicer settings."""

    binary: str = "bambu-studio"  # or "orca-slicer"
    machine_profile: str = "Bambu Lab P1S 0.4 nozzle"
    filament_profile: str = "Bambu PLA Basic"
    layer_height: float = 0.2


class Config(BaseModel):
    printer: PrinterConfig | None = None
    slicer: SlicerConfig = SlicerConfig()


def _default_path() -> Path:
    return Path.home() / ".config" / "daneel" / "config.toml"


def load(path: str | Path | None = None) -> Config:
    """Load config, falling back to defaults when no file is present."""
    p = Path(path or os.environ.get("DANEEL_CONFIG") or _default_path())
    if not p.exists():
        return Config()
    data = tomllib.loads(p.read_text())
    return Config.model_validate(data)
