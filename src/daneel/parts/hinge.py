"""Print-in-place hinge: two flat leaves joined by interleaved knuckles and a captive pin.

Printed open (both leaves flat on the bed, axis along X), so nothing needs supports and the
hinge moves straight off the plate. The pin is fused to leaf A's knuckles and runs loosely
through leaf B's, with ``clearance`` radially and ``axial_gap`` between knuckle faces.
Those two numbers are the fit: print one, free it with a few flexes, and tune.

Run directly to export an STL::

    python -m daneel.parts.hinge --out output/hinge.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq


@dataclass
class HingeParams:
    """Parameters for a print-in-place hinge. All dimensions in millimetres."""

    knuckles: int = 5  # odd, >= 3; leaf A gets the outer ones
    knuckle_length: float = 8.0
    barrel_d: float = 8.0
    pin_d: float = 3.6
    clearance: float = 0.3  # radial gap between the pin and leaf B's bores
    axial_gap: float = 0.5  # gap between neighbouring knuckles
    leaf_width: float = 20.0  # from the barrel centreline outward
    leaf_thickness: float = 3.0
    holes: int = 2  # screw holes per leaf
    hole_d: float = 3.4

    def validate(self) -> None:
        if self.knuckles < 3 or self.knuckles % 2 == 0:
            raise ValueError("knuckles must be odd and at least 3")
        if self.pin_d < 2.4:
            raise ValueError("pin_d must be at least 2.4 mm to survive flexing")
        if self.clearance < 0.15:
            raise ValueError("clearance below 0.15 mm will fuse the pin to leaf B")
        if self.axial_gap < 0.3:
            raise ValueError("axial_gap below 0.3 mm will fuse the knuckles together")
        if self.barrel_d < self.pin_d + 2 * self.clearance + 2.4:
            raise ValueError("barrel_d leaves under 1.2 mm of wall around the bore")
        if self.leaf_thickness > self.barrel_d:
            raise ValueError("leaf_thickness cannot exceed barrel_d")
        if self.leaf_width <= self.barrel_d / 2 + 3:
            raise ValueError("leaf_width too small")
        if self.knuckle_length < 3 or self.holes < 0 or self.hole_d <= 0:
            raise ValueError("knuckle_length >= 3, holes >= 0, hole_d > 0")


def _total_length(p: HingeParams) -> float:
    return p.knuckles * p.knuckle_length + (p.knuckles - 1) * p.axial_gap


def _knuckle_x(p: HingeParams, i: int) -> tuple[float, float]:
    x0 = i * (p.knuckle_length + p.axial_gap)
    return x0, x0 + p.knuckle_length


def _leaf(p: HingeParams, sign: int, owner: int) -> cq.Workplane:
    """One leaf (+1 on +Y, -1 on -Y) with the knuckles whose index parity is ``owner``."""
    r = p.barrel_d / 2
    t = p.leaf_thickness
    length = _total_length(p)
    g = p.axial_gap
    # Plate stays clear of the other leaf's barrels by the axial gap.
    edge = r + g
    plate = cq.Workplane("XY").box(length, p.leaf_width - edge, t, centered=False)
    plate = plate.translate((0, edge if sign > 0 else -p.leaf_width, 0))

    leaf = plate
    for i in range(p.knuckles):
        if i % 2 != owner:
            continue
        x0, x1 = _knuckle_x(p, i)
        barrel = cq.Workplane("YZ").workplane(offset=x0).center(0, r).circle(r).extrude(x1 - x0)
        tab = cq.Workplane("XY").box(x1 - x0, edge + 0.1, t, centered=False)
        tab = tab.translate((x0, 0 if sign > 0 else -edge - 0.1, 0))
        leaf = leaf.union(barrel).union(tab)

    if p.holes:
        hole_y = sign * (edge + (p.leaf_width - edge) / 2)
        for k in range(p.holes):
            x = length * (k + 0.5) / p.holes
            leaf = leaf.cut(cq.Workplane("XY").center(x, hole_y).circle(p.hole_d / 2).extrude(t))
    return leaf


def build(params: HingeParams | None = None) -> cq.Workplane:
    """Build the hinge as two solids: leaf A (pin included) and leaf B."""
    p = params or HingeParams()
    p.validate()
    r = p.barrel_d / 2
    length = _total_length(p)
    leaf_a = _leaf(p, -1, 0)
    leaf_b = _leaf(p, +1, 1)
    bore_r = p.pin_d / 2 + p.clearance
    for i in range(1, p.knuckles, 2):
        x0, x1 = _knuckle_x(p, i)
        bore = (
            cq.Workplane("YZ")
            .workplane(offset=x0 - 0.1)
            .center(0, r)
            .circle(bore_r)
            .extrude(x1 - x0 + 0.2)
        )
        leaf_b = leaf_b.cut(bore)
    pin = cq.Workplane("YZ").center(0, r).circle(p.pin_d / 2).extrude(length)
    leaf_a = leaf_a.union(pin)
    return cq.Workplane("XY").add(leaf_a.vals()).add(leaf_b.vals())


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a print-in-place hinge.")
    for name, default in vars(HingeParams()).items():
        ap.add_argument(f"--{name.replace('_', '-')}", type=type(default), default=default)
    ap.add_argument("--out", default="output/hinge.stl")
    args = vars(ap.parse_args())
    out = args.pop("out")
    print(f"wrote {export(build(HingeParams(**args)), out)}")


if __name__ == "__main__":
    _main()
