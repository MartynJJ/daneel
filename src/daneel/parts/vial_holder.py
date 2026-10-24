"""Vial holder: a block of pockets for upright vials, optionally tiered so back rows show.

Size it from your vial's outer diameter: ``piece="gauge"`` prints a strip of graded holes
so you can find the fit by trying a vial in each, without calipers. Pockets are
``vial_d + 2 * clearance`` wide with a lead-in chamfer, and a small push hole under each lets
you push a vial out from below. Prints flat on its base with no supports.

Run directly to export an STL::

    python -m daneel.parts.vial_holder --vial-d 15 --out output/vial_holder.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

_PIECES = ("holder", "gauge")
_GAUGE_STEP = 0.3


@dataclass
class VialHolderParams:
    """Parameters for a vial holder. All dimensions in millimetres."""

    vial_d: float = 16.0  # vial outer diameter (measure it, or print piece="gauge")
    vial_h: float = 38.0  # vial height including cap
    cols: int = 4
    rows: int = 2
    clearance: float = 0.4  # radial gap around the vial
    depth: float = 0.0  # how much of the vial each pocket holds; 0 = 55% of vial_h
    tier_step: float = 10.0  # each row further back sits this much higher (0 = flat)
    wall: float = 2.4  # between pockets and around the edge
    floor: float = 2.0
    lead_in: float = 0.8  # 45-degree chamfer at the pocket mouth
    push_hole: float = 6.0  # through-hole under each pocket (0 disables)
    piece: str = "holder"  # holder | gauge

    def validate(self) -> None:
        if self.piece not in _PIECES:
            raise ValueError(f"piece must be one of {', '.join(_PIECES)}")
        if self.vial_d <= 4 or self.vial_h <= 10:
            raise ValueError("vial_d must exceed 4 mm and vial_h 10 mm")
        if self.cols < 1 or self.rows < 1:
            raise ValueError("cols and rows must be at least 1")
        if not 0.1 <= self.clearance <= 1.0:
            raise ValueError("clearance must be between 0.1 and 1.0 mm")
        if self.wall < 1.6 or self.floor < 1.2:
            raise ValueError("wall >= 1.6 mm and floor >= 1.2 mm")
        if self.tier_step < 0 or self.lead_in < 0 or self.push_hole < 0:
            raise ValueError("tier_step, lead_in and push_hole must be non-negative")
        if self.push_hole and self.push_hole > self.vial_d - 3:
            raise ValueError("push_hole must be at least 3 mm smaller than vial_d")
        d = self.pocket_depth()
        if d < 8 or d > self.vial_h - 4:
            raise ValueError("depth must be at least 8 mm and leave 4 mm of vial exposed")

    def pocket_depth(self) -> float:
        return self.depth if self.depth > 0 else round(0.55 * self.vial_h, 1)

    def hole_d(self) -> float:
        return self.vial_d + 2 * self.clearance


def pocket(
    lead_in: float, x: float, y: float, bottom: float, top: float, hole_d: float
) -> cq.Workplane:
    """Cylindrical pocket from ``bottom`` to ``top`` with a 45-degree lead-in chamfer."""
    cyl = (
        cq.Workplane("XY")
        .workplane(offset=bottom)
        .center(x, y)
        .circle(hole_d / 2)
        .extrude(top - bottom + 1)
    )
    if lead_in:
        cone = cq.Solid.makeCone(
            hole_d / 2,
            hole_d / 2 + lead_in,
            lead_in,
            cq.Vector(x, y, top - lead_in),
            cq.Vector(0, 0, 1),
        )
        cyl = cyl.union(cq.Workplane("XY").add(cone))
    return cyl


def _holder(p: VialHolderParams) -> cq.Workplane:
    hd = p.hole_d()
    pitch = hd + p.wall
    length = p.cols * pitch + p.wall
    depth = p.pocket_depth()

    body: cq.Workplane | None = None
    prev = 0.0
    for r in range(p.rows):
        end = p.wall + r * pitch + hd
        last = r == p.rows - 1
        y1 = end + p.wall if last else end + 0.25 * p.wall
        top = p.floor + depth + r * p.tier_step
        block = (
            cq.Workplane("XY").box(length, y1 - prev, top, centered=False).translate((0, prev, 0))
        )
        body = block if body is None else body.union(block)
        prev = y1
    assert body is not None
    body = body.edges("|Z").fillet(min(2.0, p.wall * 0.8))
    body = body.faces("<Z").edges().chamfer(0.6)

    for r in range(p.rows):
        top = p.floor + depth + r * p.tier_step
        bottom = top - depth
        y = p.wall + r * pitch + hd / 2
        for c in range(p.cols):
            x = p.wall + c * pitch + hd / 2
            body = body.cut(pocket(p.lead_in, x, y, bottom, top, hd))
            if p.push_hole:
                hole = cq.Workplane("XY").center(x, y).circle(p.push_hole / 2).extrude(bottom + 0.1)
                body = body.cut(hole)
    return body


def _gauge(p: VialHolderParams) -> cq.Workplane:
    """Strip of through-holes, from 0.6 mm under to 0.6 mm over the nominal pocket size."""
    sizes = [p.hole_d() + (k - 3) * _GAUGE_STEP for k in range(7)]
    t = 5.0
    width = max(sizes) + 2 * p.wall + 6.0
    xs = []
    x = p.wall
    for s in sizes:
        xs.append(x + s / 2)
        x += s + p.wall
    length = x
    plate = cq.Workplane("XY").box(length, width, t, centered=False).edges("|Z").fillet(2.0)
    plate = plate.faces("<Z").edges().chamfer(0.5)
    for cx, s in zip(xs, sizes):
        plate = plate.cut(
            cq.Workplane("XY").center(cx, width - p.wall - s / 2).circle(s / 2).extrude(t)
        )
        plate = plate.cut(
            cq.Workplane("XY")
            .workplane(offset=t - 0.6)
            .center(cx, 4.0)
            .text(f"{s:.1f}", 3.0, 0.6, combine=False, halign="center", valign="center")
        )
    return plate


def build(params: VialHolderParams | None = None) -> cq.Workplane:
    """Build the holder, or the gauge strip when ``piece="gauge"``."""
    p = params or VialHolderParams()
    p.validate()
    return _gauge(p) if p.piece == "gauge" else _holder(p)


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a vial holder.")
    for name, default in vars(VialHolderParams()).items():
        ap.add_argument(f"--{name.replace('_', '-')}", type=type(default), default=default)
    ap.add_argument("--out", default="output/vial_holder.stl")
    args = vars(ap.parse_args())
    out = args.pop("out")
    print(f"wrote {export(build(VialHolderParams(**args)), out)}")


if __name__ == "__main__":
    _main()
