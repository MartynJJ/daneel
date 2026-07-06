"""Slicer interface — turn an exported model into a printable file.

Wraps the headless **Bambu Studio / OrcaSlicer** command-line tool (they share a
CLI lineage). Given an STL/STEP and a set of profiles, it produces a `.3mf` or
`.gcode` and parses the slicer's reported print-time and filament estimates.

    model.stl ──▶ [ slicer CLI: machine + process + filament profiles ] ──▶ model.3mf

⚠️  The exact CLI flags vary between Bambu Studio / OrcaSlicer versions. The flag
    surface is deliberately isolated in :meth:`SlicerInterface.build_command` and
    the estimate regexes in :func:`parse_estimates`, so they can be tuned against
    the installed binary. Use ``daneel slice --dry-run`` to inspect the exact
    command without executing it. Validate against a real P1S before trusting output.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from daneel.config import SlicerConfig

# export format -> slicer CLI flag
_FORMATS = {"3mf": "--export-3mf", "gcode": "--export-gcode"}

_TIME_UNITS = {"d": 1440.0, "h": 60.0, "m": 1.0, "s": 1 / 60}


class SlicerError(RuntimeError):
    """Raised when the slicer is missing, misconfigured, or fails."""


@dataclass
class SliceResult:
    output: Path
    command: list[str]
    duration_min: float | None
    grams: float | None
    stdout: str


def parse_estimates(text: str) -> tuple[float | None, float | None]:
    """Extract (duration_minutes, filament_grams) from slicer output. Best-effort."""
    duration = None
    time_match = re.search(r"(?:printing|print|estimated)\s*time[^=:\n]*[=:]\s*([0-9dhms :]+)", text, re.I)
    if time_match:
        total = sum(
            int(value) * _TIME_UNITS[unit]
            for value, unit in re.findall(r"(\d+)\s*([dhms])", time_match.group(1))
        )
        duration = round(total, 2) or None

    grams = None
    grams_match = re.search(r"filament used[^=:\n]*\[?g\]?[^=:\n]*[=:]\s*([\d.]+)", text, re.I)
    if grams_match:
        grams = float(grams_match.group(1))
    return duration, grams


class SlicerInterface:
    """Thin wrapper around the headless slicer binary."""

    def __init__(self, config: SlicerConfig | None = None) -> None:
        self.config = config or SlicerConfig()

    def resolve_binary(self) -> str:
        """Absolute path to the configured slicer binary, or raise."""
        path = shutil.which(self.config.binary)
        if not path:
            raise SlicerError(
                f"slicer binary {self.config.binary!r} not found on PATH; "
                "install Bambu Studio / OrcaSlicer or set slicer.binary in config"
            )
        return path

    def build_command(self, input_path: Path, output_path: Path) -> list[str]:
        """Construct the slicer argv. This is the version-sensitive surface."""
        fmt = self.config.export_format.lower()
        if fmt not in _FORMATS:
            raise ValueError(f"unsupported export_format {fmt!r}; use one of {sorted(_FORMATS)}")

        settings = [p for p in (self.config.machine_profile, self.config.process_profile) if p]
        cmd = [self.config.binary]
        if settings:
            cmd += ["--load-settings", ";".join(settings)]
        if self.config.filament_profile:
            cmd += ["--load-filaments", self.config.filament_profile]
        cmd += ["--slice", "0", _FORMATS[fmt], str(output_path), str(input_path)]
        return cmd

    def slice(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        dry_run: bool = False,
    ) -> SliceResult:
        """Slice `input_path`. With `dry_run`, build the command but don't execute."""
        input_path = Path(input_path)
        fmt = self.config.export_format.lower()
        out = Path(output_path) if output_path else input_path.with_suffix(f".{fmt}")
        command = self.build_command(input_path, out)

        if dry_run:
            return SliceResult(out, command, None, None, "")

        if not input_path.exists():
            raise SlicerError(f"input model not found: {input_path}")
        command[0] = self.resolve_binary()
        out.parent.mkdir(parents=True, exist_ok=True)

        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SlicerError(f"slicer exited {proc.returncode}:\n{proc.stderr.strip()}")

        duration, grams = parse_estimates(proc.stdout)
        return SliceResult(out, command, duration, grams, proc.stdout)
