"""Slicer interface — turn an exported model into a printable 3MF.

Wraps the headless **OrcaSlicer** (and compatible **Bambu Studio**) command-line
tool. Given an STL/STEP and a set of profiles it arranges the model on the plate,
slices it, and exports a `.3mf` that the P1S can print directly.

    model.stl ──▶ [ orca-slicer: machine + process + filament profiles ] ──▶ model.3mf

The command surface below was validated against **OrcaSlicer 2.4.1** on a real
P1S profile set. Notes from that validation:

* There is **no** ``--export-gcode`` flag; the sliced G-code is embedded in the
  3MF (which is also what the printer consumes), so 3MF is the only export target.
* ``--arrange 1 --slice 0`` are required (place on plate, slice all plates).
* Print-time / filament estimates are **not** printed to stdout — they live inside
  the 3MF at ``Metadata/slice_info.config`` (``prediction`` seconds, filament
  ``used_g`` grams). :func:`read_3mf_estimates` reads them back.
* The process profile must list the target printer in its ``compatible_printers``.
  For the P1S that is the ``@BBL X1C`` process presets (Bambu groups them there).

Use ``daneel slice --dry-run`` to inspect the exact command without executing.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from daneel.config import SlicerConfig


class SlicerError(RuntimeError):
    """Raised when the slicer is missing, misconfigured, or fails."""


@dataclass
class SliceResult:
    output: Path
    command: list[str]
    duration_min: float | None
    grams: float | None
    stdout: str


def read_3mf_estimates(path: str | Path) -> tuple[float | None, float | None]:
    """Read (duration_minutes, filament_grams) from a sliced 3MF. Best-effort.

    Estimates live in ``Metadata/slice_info.config``: per-plate ``prediction``
    (seconds) and per-filament ``used_g`` (grams). The headless CLI leaves
    ``used_g`` at 0 for *system* profiles (it doesn't resolve their inherited
    density), so as a fallback grams is computed from the embedded G-code header
    (``filament used [cm3]`` × ``filament_density``). Grams is ``None`` when
    neither source yields a positive value — use a flattened/exported filament
    profile (density baked in) if you need weight.
    """
    with zipfile.ZipFile(path) as archive:
        name = next((n for n in archive.namelist() if n.lower().endswith("slice_info.config")), None)
        if name is None:
            return None, None
        root = ET.fromstring(archive.read(name))

        duration: float | None = None
        grams = 0.0
        for plate in root.iterfind("plate"):
            for meta in plate.iterfind("metadata"):
                if meta.get("key") == "prediction" and meta.get("value"):
                    try:
                        duration = (duration or 0.0) + float(meta.get("value")) / 60
                    except ValueError:
                        pass
            for filament in plate.iterfind("filament"):
                try:
                    grams += float(filament.get("used_g") or 0)
                except ValueError:
                    pass

        if grams <= 0:
            grams = _grams_from_gcode(archive) or 0.0

    return (
        round(duration, 1) if duration else None,
        round(grams, 2) if grams > 0 else None,
    )


def _grams_from_gcode(archive: zipfile.ZipFile) -> float | None:
    """Fallback: grams = filament volume (cm3) × density, read from the G-code header."""
    name = next((n for n in archive.namelist() if n.lower().endswith(".gcode")), None)
    if name is None:
        return None
    text = archive.read(name).decode("utf-8", "replace")

    def _find(pattern: str) -> float | None:
        match = re.search(pattern, text, re.I)
        return float(match.group(1)) if match else None

    cm3 = _find(r"filament used \[cm3\]\s*=\s*([\d.]+)")
    density = _find(r"filament_density\s*[:=]\s*([\d.]+)")
    if cm3 and density and density > 0:
        return cm3 * density
    return None


class SlicerInterface:
    """Thin wrapper around the headless OrcaSlicer / Bambu Studio binary."""

    def __init__(self, config: SlicerConfig | None = None) -> None:
        self.config = config or SlicerConfig()

    def resolve_binary(self) -> str:
        """Absolute path to the configured slicer binary, or raise."""
        path = shutil.which(self.config.binary)
        if not path:
            raise SlicerError(
                f"slicer binary {self.config.binary!r} not found on PATH; "
                "install OrcaSlicer / Bambu Studio or set slicer.binary in config"
            )
        return path

    def build_command(self, input_path: Path, output_path: Path) -> list[str]:
        """Construct the slicer argv. This is the version-sensitive surface."""
        if self.config.export_format.lower() != "3mf":
            raise ValueError(
                "the OrcaSlicer CLI exports print estimates only via 3MF "
                "(no --export-gcode); set slicer.export_format = '3mf'"
            )
        settings = [p for p in (self.config.machine_profile, self.config.process_profile) if p]
        cmd = [self.config.binary]
        if settings:
            cmd += ["--load-settings", ";".join(settings)]
        if self.config.filament_profile:
            cmd += ["--load-filaments", self.config.filament_profile]
        cmd += ["--arrange", "1", "--slice", "0", "--export-3mf", str(output_path), str(input_path)]
        return cmd

    def slice(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        dry_run: bool = False,
    ) -> SliceResult:
        """Slice `input_path` to a 3MF. With `dry_run`, build the command but don't run it."""
        input_path = Path(input_path)
        out = Path(output_path) if output_path else input_path.with_suffix(".3mf")
        command = self.build_command(input_path, out)

        if dry_run:
            return SliceResult(out, command, None, None, "")

        if not input_path.exists():
            raise SlicerError(f"input model not found: {input_path}")
        command[0] = self.resolve_binary()
        out.parent.mkdir(parents=True, exist_ok=True)

        proc = subprocess.run(command, capture_output=True, text=True)
        if proc.returncode != 0 or not out.exists():
            tail = "\n".join(proc.stdout.strip().splitlines()[-8:])
            raise SlicerError(f"slicer exited {proc.returncode}; last output:\n{tail}")

        duration, grams = read_3mf_estimates(out)
        return SliceResult(out, command, duration, grams, proc.stdout)
