"""ArUco marker sheet generation for the calibration cube.

Emits a print-at-100% SVG sheet of ArUco markers, one per pocketed cube face, sized
to the cube's pocket so each marker drops flush into its recess. The marker bit
patterns come from OpenCV's predefined dictionaries (optional ``[scan]`` extra);
we render them as crisp **vector** rects at exact millimetre size rather than
embedding a raster, so they print sharp at any DPI.

    from daneel.parts import markers
    markers.write_marker_sheet(params, "output/calib_cube_markers.svg")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from daneel.parts.calib_cube import CalibCubeParams

# Physical page sizes (mm).
_PAGES = {"a4": (210.0, 297.0), "letter": (216.0, 279.0)}

_DICTS = {
    "4x4_50": "DICT_4X4_50",
    "4x4_100": "DICT_4X4_100",
    "5x5_50": "DICT_5X5_50",
    "6x6_50": "DICT_6X6_50",
}


def _marker_grid(dictionary: str, marker_id: int) -> list[list[int]]:
    """Return the marker as an NxN grid, 1 = black cell (incl. the black border).

    Requires opencv (the ``[scan]`` extra). Raises a clear error if missing.
    """
    try:
        import cv2  # type: ignore
        import numpy as np  # noqa: F401
    except ImportError as e:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "marker generation needs OpenCV — install the extra:  pip install -e '.[scan]'"
        ) from e

    if dictionary not in _DICTS:
        raise ValueError(f"unknown dict {dictionary!r}; use one of {sorted(_DICTS)}")
    aruco = cv2.aruco
    d = aruco.getPredefinedDictionary(getattr(aruco, _DICTS[dictionary]))
    bits = int(dictionary.split("_")[0].split("x")[0])
    side = bits + 2  # one border cell each side
    gen = getattr(aruco, "generateImageMarker", None) or getattr(aruco, "drawMarker")
    img = gen(d, int(marker_id), side)  # side x side, 0=black 255=white
    return [[1 if img[r][c] < 128 else 0 for c in range(side)] for r in range(side)]


def _marker_svg(
    marker_id: int, x: float, y: float, size: float, grid: list[list[int]], label: str
) -> str:
    """SVG fragment: a white marker tile with black cells, plus a label, at (x,y) mm."""
    n = len(grid)
    cell = size / n
    parts = [f'<rect x="{x:.3f}" y="{y:.3f}" width="{size:.3f}" height="{size:.3f}" fill="#fff"/>']
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                parts.append(
                    f'<rect x="{x + c * cell:.3f}" y="{y + r * cell:.3f}" '
                    f'width="{cell:.3f}" height="{cell:.3f}" fill="#000"/>'
                )
    parts.append(
        f'<text x="{x + size / 2:.3f}" y="{y + size + 5:.2f}" font-family="monospace" '
        f'font-size="3.5" text-anchor="middle" fill="#000">{label}  ·  id {marker_id}</text>'
    )
    # cut guide
    parts.append(
        f'<rect x="{x - 0.5:.3f}" y="{y - 0.5:.3f}" width="{size + 1:.3f}" height="{size + 1:.3f}" '
        f'fill="none" stroke="#bbb" stroke-width="0.15" stroke-dasharray="1 1"/>'
    )
    return "\n".join(parts)


def write_marker_sheet(
    params: "CalibCubeParams",
    out: str | Path,
    dictionary: str = "4x4_50",
    page: str = "a4",
    marker_ids: list[int] | None = None,
) -> Path:
    """Write an SVG marker sheet for the cube's pocketed faces. Print at 100% (no scaling)."""
    from daneel.parts.calib_cube import FACES

    if page not in _PAGES:
        raise ValueError(f"unknown page {page!r}; use one of {sorted(_PAGES)}")
    pw, ph = _PAGES[page]
    ids = marker_ids or list(range(len(FACES)))
    if len(ids) != len(FACES):
        raise ValueError(f"need {len(FACES)} marker ids, got {len(ids)}")

    m = params.pocket_side  # marker printed size = pocket size (drops into the recess)
    margin, gap_y = 15.0, 12.0
    cols = 2
    col_w = m + 20.0
    x0 = (pw - (cols * col_w)) / 2 + 10.0

    body = [
        f'<rect x="0" y="0" width="{pw}" height="{ph}" fill="#fff"/>',
        f'<text x="{pw / 2:.1f}" y="10" font-family="monospace" font-size="4.5" '
        f'text-anchor="middle" fill="#000">daneel calib_cube — print at 100% (no scaling)  ·  '
        f"{dictionary}  ·  marker {m:.1f} mm</text>",
    ]
    for i, (face, mid) in enumerate(zip(FACES, ids)):
        col, row = i % cols, i // cols
        x = x0 + col * col_w
        y = margin + row * (m + gap_y + 6)
        body.append(_marker_svg(mid, x, y, m, _marker_grid(dictionary, mid), face))

    # 50 mm scale bar for a caliper sanity-check
    by = ph - 18.0
    body.append(
        f'<line x1="{margin}" y1="{by}" x2="{margin + 50}" y2="{by}" stroke="#000" stroke-width="0.4"/>'
        f'<line x1="{margin}" y1="{by - 2}" x2="{margin}" y2="{by + 2}" stroke="#000" stroke-width="0.4"/>'
        f'<line x1="{margin + 50}" y1="{by - 2}" x2="{margin + 50}" y2="{by + 2}" stroke="#000" stroke-width="0.4"/>'
        f'<text x="{margin + 25}" y="{by - 3}" font-family="monospace" font-size="3.5" '
        f'text-anchor="middle" fill="#000">50 mm — verify with calipers</text>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}mm" height="{ph}mm" '
        f'viewBox="0 0 {pw} {ph}">\n' + "\n".join(body) + "\n</svg>\n"
    )
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    return path
