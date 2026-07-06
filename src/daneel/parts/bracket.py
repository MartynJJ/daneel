"""Parametric L-shaped angle bracket with mounting holes.

Two perpendicular legs meeting at a right angle, with evenly spaced through-holes
on each leg for fastening. A staple functional print.

Run directly to export an STL::

    python -m daneel.parts.bracket --leg-a 40 --leg-b 60 --out output/bracket.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq


@dataclass
class BracketParams:
    """Parameters for an L-bracket. All dimensions in millimetres."""

    leg_a: float = 40.0  # vertical leg length (Z)
    leg_b: float = 60.0  # horizontal leg length (X)
    width: float = 25.0  # depth of both legs (Y)
    thickness: float = 4.0  # material thickness
    hole_diameter: float = 5.0
    holes_per_leg: int = 2
    hole_margin: float = 8.0  # clearance from leg tip / corner to hole centre

    def validate(self) -> None:
        if min(self.leg_a, self.leg_b, self.width, self.thickness) <= 0:
            raise ValueError("leg_a, leg_b, width and thickness must be positive")
        if self.holes_per_leg < 0:
            raise ValueError("holes_per_leg cannot be negative")
        if self.hole_diameter >= self.width:
            raise ValueError("hole_diameter must be smaller than the leg width")
        if self.thickness + self.hole_margin >= min(self.leg_a, self.leg_b):
            raise ValueError("legs too short for the requested hole_margin")


def _linspace(lo: float, hi: float, n: int) -> list[float]:
    """n evenly spaced points in [lo, hi]; single point is centred."""
    if n <= 0:
        return []
    if n == 1:
        return [(lo + hi) / 2]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def build(params: BracketParams | None = None) -> cq.Workplane:
    """Build the bracket and return a CadQuery Workplane."""
    p = params or BracketParams()
    p.validate()

    horiz = cq.Workplane("XY").box(p.leg_b, p.width, p.thickness, centered=False)
    vert = cq.Workplane("XY").box(p.thickness, p.width, p.leg_a, centered=False)
    bracket = horiz.union(vert)

    r = p.hole_diameter / 2

    # Horizontal-leg holes: drilled through Z, spaced along X.
    for x in _linspace(p.thickness + p.hole_margin, p.leg_b - p.hole_margin, p.holes_per_leg):
        cutter = (
            cq.Workplane("XY")
            .moveTo(x, p.width / 2)
            .circle(r)
            .extrude(p.thickness + 0.2)
            .translate((0, 0, -0.1))
        )
        bracket = bracket.cut(cutter)

    # Vertical-leg holes: drilled through the thickness (X), spaced along Z.
    # (Must pierce the 4 mm thickness, not the width — otherwise a hole wider than
    # the thickness severs the leg and leaves empty layers that won't slice.)
    for z in _linspace(p.thickness + p.hole_margin, p.leg_a - p.hole_margin, p.holes_per_leg):
        cutter = (
            cq.Workplane("YZ")
            .workplane(offset=-0.1)
            .center(p.width / 2, z)
            .circle(r)
            .extrude(p.thickness + 0.2)
        )
        bracket = bracket.cut(cutter)

    return bracket


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a parametric L-bracket.")
    ap.add_argument("--leg-a", type=float, default=40.0)
    ap.add_argument("--leg-b", type=float, default=60.0)
    ap.add_argument("--width", type=float, default=25.0)
    ap.add_argument("--thickness", type=float, default=4.0)
    ap.add_argument("--hole-diameter", type=float, default=5.0)
    ap.add_argument("--holes-per-leg", type=int, default=2)
    ap.add_argument("--out", default="output/bracket.stl")
    args = ap.parse_args()

    params = BracketParams(
        leg_a=args.leg_a,
        leg_b=args.leg_b,
        width=args.width,
        thickness=args.thickness,
        hole_diameter=args.hole_diameter,
        holes_per_leg=args.holes_per_leg,
    )
    path = export(build(params), args.out)
    print(f"wrote {path}")


if __name__ == "__main__":
    _main()
