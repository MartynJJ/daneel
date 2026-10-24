"""Screw-top vial case: a threaded jar whose floor is moulded with upright vial pockets.

The jar is sized from the vial: pockets are spaced round a circle (a 2 x 2 square for four
vials), the body is tall enough that the vials sit below the rim, and the lid is the proven
jar lid. Prints like ``jar``: body open end up, lid plate-down, no supports.

Run directly to export an STL::

    python -m daneel.parts.vial_case --count 4 --out output/vial_case.stl
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from daneel.parts.jar import JarParams, _volume
from daneel.parts.jar import build as build_jar
from daneel.parts.vial_holder import pocket

_PIECES = ("both", "body", "lid")
_BASE = 2.0  # solid floor under the pockets
_TOP_ROOM = 2.0  # vial tops sit this far below the rim


@dataclass
class VialCaseParams:
    """Parameters for a screw-top vial case. All dimensions in millimetres."""

    vial_d: float = 16.0
    vial_h: float = 38.0  # including cap
    count: int = 4  # 1 to 6 vials
    clearance: float = 0.4  # radial gap around each vial
    pocket_depth: float = 12.0  # how far each vial sits into the floor
    vial_gap: float = 1.2  # wall between neighbouring pockets
    wall: float = 3.0
    thread_pitch: float = 3.0
    thread_depth: float = 1.2
    thread_height: float = 10.0
    jar_clearance: float = 0.3  # thread/lid fit (proven at 0.3 on the P1S)
    lead_in: float = 0.8
    push_hole: float = 6.0  # through-hole under each pocket (0 disables)
    grip: int = 24
    gap: float = 8.0
    piece: str = "both"  # both | body | lid

    def validate(self) -> None:
        if self.piece not in _PIECES:
            raise ValueError(f"piece must be one of {', '.join(_PIECES)}")
        if not 1 <= self.count <= 6:
            raise ValueError("count must be between 1 and 6")
        if self.vial_d <= 4 or self.vial_h <= 10:
            raise ValueError("vial_d must exceed 4 mm and vial_h 10 mm")
        if not 0.1 <= self.clearance <= 1.0:
            raise ValueError("clearance must be between 0.1 and 1.0 mm")
        if self.pocket_depth < 6 or self.pocket_depth > self.vial_h - 6:
            raise ValueError("pocket_depth must be at least 6 mm and leave 6 mm of vial exposed")
        if self.vial_gap < 1.2:
            raise ValueError("vial_gap must be at least 1.2 mm")
        if self.push_hole and self.push_hole > self.vial_d - 3:
            raise ValueError("push_hole must be at least 3 mm smaller than vial_d")
        self.jar(piece="both").validate()

    def hole_d(self) -> float:
        return self.vial_d + 2 * self.clearance

    def ring_radius(self) -> float:
        """Radius of the circle through the pocket centres."""
        if self.count == 1:
            return 0.0
        pitch = self.hole_d() + self.vial_gap
        if self.count == 2:
            return pitch / 2
        return pitch / (2 * math.sin(math.pi / self.count))

    def centres(self) -> list[tuple[float, float]]:
        r = self.ring_radius()
        start = math.pi / 4 if self.count == 4 else math.pi / 2
        return [
            (
                r * math.cos(start + 2 * math.pi * i / self.count),
                r * math.sin(start + 2 * math.pi * i / self.count),
            )
            for i in range(self.count)
        ]

    def outer_d(self) -> float:
        return 2 * (self.ring_radius() + self.hole_d() / 2 + 0.6 + self.wall)

    def floor_top(self) -> float:
        return _BASE + self.pocket_depth

    def height(self) -> float:
        return _BASE + self.vial_h + _TOP_ROOM

    def jar(self, piece: str) -> JarParams:
        return JarParams(
            outer_d=round(self.outer_d(), 1),
            height=self.height(),
            wall=self.wall,
            floor=self.floor_top(),
            thread_pitch=self.thread_pitch,
            thread_depth=self.thread_depth,
            thread_height=self.thread_height,
            clearance=self.jar_clearance,
            grip=self.grip,
            gap=self.gap,
            piece=piece,
        )


def _body(p: VialCaseParams) -> cq.Workplane:
    body = build_jar(p.jar("body"))
    before = _volume(body)
    hd = p.hole_d()
    for x, y in p.centres():
        body = body.cut(pocket(p.lead_in, x, y, _BASE, p.floor_top(), hd), tol=1e-4)
        if p.push_hole:
            hole = cq.Workplane("XY").center(x, y).circle(p.push_hole / 2).extrude(_BASE + 0.1)
            body = body.cut(hole, tol=1e-4)
    if _volume(body) > before - 0.5 * p.count * math.pi * (hd / 2) ** 2 * p.pocket_depth:
        raise RuntimeError("vial pockets did not cut; adjust the parameters slightly")
    return body


def build(params: VialCaseParams | None = None) -> cq.Workplane:
    """Build the case; ``piece`` selects body, lid, or both side by side."""
    p = params or VialCaseParams()
    p.validate()
    if p.piece == "lid":
        return build_jar(p.jar("lid"))
    body = _body(p)
    if p.piece == "body":
        return body
    jar = p.jar("both")
    r = jar.outer_d / 2
    r_lid = r + jar.lid_wall
    lid = build_jar(p.jar("lid")).translate((r_lid + p.gap / 2, 0, 0))
    body = body.translate((-(r + p.gap / 2), 0, 0))
    return cq.Workplane("XY").add(body.vals()).add(lid.vals())


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a screw-top vial case.")
    for name, default in vars(VialCaseParams()).items():
        ap.add_argument(f"--{name.replace('_', '-')}", type=type(default), default=default)
    ap.add_argument("--out", default="output/vial_case.stl")
    args = vars(ap.parse_args())
    out = args.pop("out")
    print(f"wrote {export(build(VialCaseParams(**args)), out)}")


if __name__ == "__main__":
    _main()
