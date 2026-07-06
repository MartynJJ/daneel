"""Parametric open-top box / container.

A rectangular container with a solid floor and four walls, open at the top.
Good for bins, trays, and drawer organizers.

Run directly to export an STL::

    python -m daneel.parts.box --length 80 --width 50 --height 30 --out output/box.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq


@dataclass
class BoxParams:
    """Parameters for an open-top box. All dimensions in millimetres."""

    length: float = 80.0  # outer X
    width: float = 50.0  # outer Y
    height: float = 30.0  # outer Z
    wall: float = 2.0  # side wall thickness
    floor: float = 2.0  # floor thickness
    fillet: float = 2.0  # vertical edge fillet (0 to disable)

    def validate(self) -> None:
        if min(self.length, self.width, self.height) <= 0:
            raise ValueError("length, width and height must be positive")
        if self.wall <= 0 or self.floor <= 0:
            raise ValueError("wall and floor must be positive")
        if 2 * self.wall >= min(self.length, self.width):
            raise ValueError("walls too thick for the box footprint")
        if self.floor >= self.height:
            raise ValueError("floor must be thinner than the box height")
        if self.fillet * 2 >= min(self.length, self.width):
            raise ValueError("fillet too large for the box footprint")


def build(params: BoxParams | None = None) -> cq.Workplane:
    """Build the box and return a CadQuery Workplane."""
    p = params or BoxParams()
    p.validate()

    outer = cq.Workplane("XY").box(p.length, p.width, p.height, centered=(True, True, False))
    if p.fillet > 0:
        outer = outer.edges("|Z").fillet(p.fillet)

    # Cavity: start above the floor, overshoot the top so it opens fully.
    cavity = cq.Workplane("XY").workplane(offset=p.floor).box(
        p.length - 2 * p.wall,
        p.width - 2 * p.wall,
        p.height,  # > remaining height, so the top is left open
        centered=(True, True, False),
    )
    inner_fillet = max(p.fillet - p.wall, 0)
    if inner_fillet > 0:
        cavity = cavity.edges("|Z").fillet(inner_fillet)

    return outer.cut(cavity)


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a parametric open-top box.")
    ap.add_argument("--length", type=float, default=80.0)
    ap.add_argument("--width", type=float, default=50.0)
    ap.add_argument("--height", type=float, default=30.0)
    ap.add_argument("--wall", type=float, default=2.0)
    ap.add_argument("--floor", type=float, default=2.0)
    ap.add_argument("--fillet", type=float, default=2.0)
    ap.add_argument("--out", default="output/box.stl")
    args = ap.parse_args()

    params = BoxParams(
        length=args.length,
        width=args.width,
        height=args.height,
        wall=args.wall,
        floor=args.floor,
        fillet=args.fillet,
    )
    path = export(build(params), args.out)
    print(f"wrote {path}")


if __name__ == "__main__":
    _main()
