"""Hex cap for an exposed nut, printed upside down so it needs no supports.

The closed end lies flat on the bed and the pocket opens upward. The round flange at the
open end flares out on a 45 degree cone, so nothing overhangs more than the slicer can
bridge. Dimensions were estimated from the toolpaths of a commercial-style M14 scooter-axle
cover, so check ``nut_af`` and ``pocket_depth`` against the real nut before gluing.

Run directly to export an STL::

    python -m daneel.parts.nut_cover --out output/nut_cover.stl
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq


@dataclass
class NutCoverParams:
    """Parameters for a hex nut cap. All dimensions in millimetres."""

    nut_af: float = 21.3  # pocket across flats (M14 nut is 21 mm AF plus slack)
    outer_af: float = 27.5  # outer hex across flats
    height: float = 20.6
    pocket_depth: float = 16.8
    flange_d: float = 35.0  # round skirt at the open end
    flange_t: float = 6.3
    lead_in: float = 0.8  # chamfer at the pocket mouth
    count: int = 1  # caps per plate, in a row
    gap: float = 6.0  # spacing between caps when count > 1

    def validate(self) -> None:
        if self.nut_af < 5:
            raise ValueError("nut_af must be at least 5 mm")
        if self.outer_af < self.nut_af + 4:
            raise ValueError("outer_af must exceed nut_af by at least 4 mm (2 mm walls)")
        if self.height < self.pocket_depth + 2:
            raise ValueError("height must exceed pocket_depth by at least 2 mm (roof)")
        if self.flange_d <= self.outer_af / math.cos(math.radians(30)):
            raise ValueError("flange_d must exceed the outer hex across corners")
        cone = (self.flange_d - self.outer_af) / 2
        if self.flange_t < cone + 1.5:
            raise ValueError(f"flange_t must be at least {cone + 1.5:.1f} mm for a 45 degree cone")
        if self.flange_t > self.height - 2:
            raise ValueError("flange_t leaves under 2 mm of body")
        if not 0 <= self.lead_in <= 2 or self.gap < 3 or not 1 <= self.count <= 6:
            raise ValueError("lead_in 0-2 mm, gap >= 3 mm, count 1-6")


def _hex(af: float) -> cq.Workplane:
    return cq.Workplane("XY").polygon(6, af / math.cos(math.radians(30)))


def _cap(p: NutCoverParams) -> cq.Workplane:
    z0 = p.height - p.flange_t
    r_flat = p.outer_af / 2
    r_out = p.flange_d / 2
    rise = r_out - r_flat
    body = _hex(p.outer_af).extrude(p.height)
    skirt = (
        cq.Workplane("XZ")
        .polyline([(0, z0), (r_flat, z0), (r_out, z0 + rise), (r_out, p.height), (0, p.height)])
        .close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    cap = body.union(skirt)
    pocket = _hex(p.nut_af).extrude(-p.pocket_depth).translate((0, 0, p.height))
    cap = cap.cut(pocket)
    if p.lead_in:
        cap = cap.faces(">Z").edges("not %CIRCLE").chamfer(p.lead_in)
    return cap


def build(params: NutCoverParams) -> cq.Workplane:
    params.validate()
    p = params
    pitch = p.flange_d + p.gap
    out = _cap(p).translate((-(p.count - 1) * pitch / 2, 0, 0))
    for i in range(1, p.count):
        out = out.union(_cap(p).translate((-(p.count - 1) * pitch / 2 + i * pitch, 0, 0)))
    return out


if __name__ == "__main__":
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output/nut_cover.stl")
    args = ap.parse_args()
    print(export(build(NutCoverParams()), args.out))
