"""Pre-flight preview — render the real toolpaths of a sliced 3MF as a self-contained page.

The page is built from the G-code embedded in the 3MF (``Metadata/plate_1.gcode``), so
it shows what the printer will actually do, including anything the slicer got wrong.
It has no external dependencies: open the HTML in any browser, or serve it statically.

Assumes Bambu-style G-code: relative extrusion (``M83``) and ``; Z_HEIGHT:`` layer markers.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from daneel.slice import read_3mf_estimates

_TEMPLATE = Path(__file__).with_name("data") / "preview_template.html"
_WORD = re.compile(r"([XYZE])(-?\d*\.?\d+)")
_PLACEHOLDER = "/*__DATA__*/null"


class PreviewError(RuntimeError):
    pass


def extract_layers(gcode: str) -> list[dict]:
    """Per-layer extrusion segments ``[x1, y1, x2, y2]``, in bed coordinates.

    Only moves after the first layer marker count, so the start-sequence purge and
    load line are excluded. Arcs (G2/G3) are drawn as chords.
    """
    layers: list[dict] = []
    x = y = 0.0
    z = 0.0
    started = False
    for raw in gcode.splitlines():
        if raw.startswith("; Z_HEIGHT:"):
            started = True
            z = float(raw.split(":", 1)[1])
            layers.append({"z": z, "segs": []})
            continue
        if not raw or raw[0] != "G":
            continue
        code = raw.split(None, 1)[0]
        if code not in ("G0", "G1", "G2", "G3"):
            continue
        words = {k: float(v) for k, v in _WORD.findall(raw.split(";", 1)[0])}
        nx, ny = words.get("X", x), words.get("Y", y)
        if started and words.get("E", 0.0) > 0 and (nx, ny) != (x, y):
            layers[-1]["segs"].append([x, y, nx, ny])
        x, y = nx, ny
    return [layer for layer in layers if layer["segs"]]


def build_data(part: str, layers: list[dict], est_min: float | None, grams: float | None) -> dict:
    """Centre the toolpaths on their footprint and package them for the viewer."""
    xs = [v for layer in layers for s in layer["segs"] for v in (s[0], s[2])]
    ys = [v for layer in layers for s in layer["segs"] for v in (s[1], s[3])]
    if not xs:
        raise PreviewError("no extrusion moves found in the G-code")
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    out = []
    for layer in layers:
        segs = [
            [round(s[0] - cx, 2), round(s[1] - cy, 2), round(s[2] - cx, 2), round(s[3] - cy, 2)]
            for s in layer["segs"]
        ]
        out.append({"z": layer["z"], "segs": segs})
    return {
        "part": part,
        "est_min": round(est_min) if est_min else None,
        "grams": grams,
        "z_height": layers[-1]["z"],
        "bbox": [round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)],
        "layers": out,
    }


def render_html(data: dict) -> str:
    template = _TEMPLATE.read_text()
    if _PLACEHOLDER not in template:
        raise PreviewError("preview template is missing its data placeholder")
    # "</" would end the inline <script> early if it ever appeared in a string.
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return template.replace(_PLACEHOLDER, blob, 1)


def preview_3mf(path: str | Path, out: str | Path | None = None, part: str | None = None) -> Path:
    """Write ``<stem>_preview.html`` (or ``out``) for a sliced 3MF; returns its path."""
    path = Path(path)
    try:
        with zipfile.ZipFile(path) as z:
            name = next((n for n in z.namelist() if n.endswith("plate_1.gcode")), None)
            if name is None:
                raise PreviewError(f"{path.name} has no embedded G-code (was it sliced?)")
            gcode = z.read(name).decode("utf-8", "replace")
    except (OSError, zipfile.BadZipFile) as exc:
        raise PreviewError(f"cannot read {path}: {exc}") from exc
    minutes, grams = read_3mf_estimates(path)
    data = build_data(part or path.stem, extract_layers(gcode), minutes, grams)
    dst = Path(out) if out else path.with_name(f"{path.stem}_preview.html")
    dst.write_text(render_html(data))
    return dst
