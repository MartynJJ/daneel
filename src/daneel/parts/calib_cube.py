"""Parametric photogrammetry calibration cube.

A cube of known edge length with a recessed square pocket on five faces (top and
the four sides; the bottom is left flat so it prints on the bed without bridging a
downward pocket). Each pocket seats a laser-printed ArUco marker — see
``daneel.parts.markers`` for the companion marker sheet. One vertical corner is
chamfered to key the coordinate frame.

Printed, the cube gives a photogrammetry solver absolute **scale** (measure the real
print with calipers and use that, not nominal) and the markers give it robust
**fiducials**. Print in matte white / light PLA — gloss and dark colours hurt
marker detection.

Run directly to export the STL *and* the marker sheet::

    python -m daneel.parts.calib_cube --size 40 --out output/calib_cube.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

# Face order matches the marker IDs on the companion sheet.
FACES = ("top", "+x", "-x", "+y", "-y")


@dataclass
class CalibCubeParams:
    """Parameters for a calibration cube. All dimensions in millimetres."""

    size: float = 40.0  # cube edge — the metric reference
    pocket_margin: float = 4.0  # border from face edge to pocket (marker quiet zone)
    recess_depth: float = 0.6  # pocket depth, to seat a marker card flush
    origin_chamfer: float = 3.0  # chamfer on one vertical corner to key orientation

    def validate(self) -> None:
        if self.size <= 0:
            raise ValueError("size must be positive")
        if self.pocket_margin <= 0 or 2 * self.pocket_margin >= self.size:
            raise ValueError("pocket_margin too large for the cube face")
        if self.recess_depth <= 0 or self.recess_depth >= self.size / 2:
            raise ValueError("recess_depth must be positive and < size/2")
        if self.origin_chamfer < 0:
            raise ValueError("origin_chamfer cannot be negative")
        if self.origin_chamfer >= self.pocket_margin:
            raise ValueError("origin_chamfer must be < pocket_margin so it clears the pockets")

    @property
    def pocket_side(self) -> float:
        return self.size - 2 * self.pocket_margin


def build(params: CalibCubeParams | None = None) -> cq.Workplane:
    """Build the calibration cube and return a CadQuery Workplane.

    The solid is centred in XY and sits on the bed (bottom face at z=0).
    """
    p = params or CalibCubeParams()
    p.validate()
    s, d, pk = p.size, p.recess_depth, p.pocket_side

    cube = cq.Workplane("XY").box(s, s, s, centered=(True, True, True))

    # Canonical pocket cutter flush to the +Z face, cutting `d` deep.
    top = (
        cq.Workplane("XY")
        .box(pk, pk, d, centered=(True, True, True))
        .translate((0, 0, s / 2 - d / 2))
    )
    cutters = {
        "top": top,
        "+x": top.rotate((0, 0, 0), (0, 1, 0), 90),
        "-x": top.rotate((0, 0, 0), (0, 1, 0), -90),
        "+y": top.rotate((0, 0, 0), (1, 0, 0), -90),
        "-y": top.rotate((0, 0, 0), (1, 0, 0), 90),
    }
    for c in cutters.values():
        cube = cube.cut(c)

    # Key the orientation: chamfer the single vertical corner edge at (+X,+Y).
    if p.origin_chamfer > 0:
        cube = cube.edges("|Z").edges(">X").edges(">Y").chamfer(p.origin_chamfer)

    return cube.translate((0, 0, s / 2))  # bottom on the bed


def companions(params: CalibCubeParams, out_path) -> list:
    """Write companion artifacts next to the STL — here, the ArUco marker sheet.

    Picked up automatically by `daneel make` (see registry.companions).
    """
    from pathlib import Path

    from daneel.parts import markers

    out_path = Path(out_path)
    sheet = out_path.with_name(out_path.stem + "_markers.svg")
    markers.write_marker_sheet(params, sheet)
    return [sheet]


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a photogrammetry calibration cube.")
    ap.add_argument("--size", type=float, default=40.0)
    ap.add_argument("--pocket-margin", type=float, default=4.0)
    ap.add_argument("--recess-depth", type=float, default=0.6)
    ap.add_argument("--origin-chamfer", type=float, default=3.0)
    ap.add_argument("--out", default="output/calib_cube.stl")
    ap.add_argument("--sheet", default=None, help="marker sheet path (default: alongside --out)")
    ap.add_argument("--dict", default="4x4_50", dest="dictionary")
    args = ap.parse_args()

    params = CalibCubeParams(
        size=args.size,
        pocket_margin=args.pocket_margin,
        recess_depth=args.recess_depth,
        origin_chamfer=args.origin_chamfer,
    )
    path = export(build(params), args.out)
    print(f"wrote {path}")

    from pathlib import Path

    from daneel.parts import markers

    sheet = Path(args.sheet) if args.sheet else path.with_name(path.stem + "_markers.svg")
    markers.write_marker_sheet(params, sheet, dictionary=args.dictionary)
    print(f"wrote {sheet}")


if __name__ == "__main__":
    _main()
