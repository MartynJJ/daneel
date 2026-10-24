"""Printable surface patterns: cutter solids for a cylindrical wall or a flat disc face.

Every cutter has 45-degree walls (or is a half-round groove) so the finished surface prints
without supports. Cutters are returned as one compound so a single boolean applies them all.

``WALL_PATTERNS`` work on a vertical cylinder wall; ``FACE_PATTERNS`` on a flat face that
prints against the bed, where only V-shaped recesses are safe.
"""

from __future__ import annotations

import math
from typing import cast

import cadquery as cq

WALL_PATTERNS = ("none", "flutes", "hex", "diamond", "rings")
FACE_PATTERNS = ("none", "hex", "rings", "rays")
_OUT = 0.3  # cutters extend this far outside the surface so the cut is clean


def _frustum(sides: int, apothem: float, depth: float) -> cq.Workplane:
    """Pyramid recess, surface plane z=0, narrow end at z=-depth, flaring out to z=+_OUT.

    Walls are 45 degrees. Vertices sit on the local x axis.
    """
    k = 1.0 / math.cos(math.pi / sides)

    def ring(ap: float, z: float) -> cq.Wire:
        r = ap * k
        pts = [
            cq.Vector(
                r * math.cos(2 * math.pi * i / sides), r * math.sin(2 * math.pi * i / sides), z
            )
            for i in range(sides)
        ]
        return cq.Wire.makePolygon(pts + [pts[0]])

    solid = cq.Solid.makeLoft([ring(apothem - depth, -depth), ring(apothem + _OUT, _OUT)])
    return cq.Workplane("XY").add(solid)


def _lattice(sides: int, size: float, gap: float) -> tuple[float, float, float]:
    """(apothem, pitch across, pitch between rows) for a staggered lattice of cells."""
    if sides == 6:
        apothem = size / 2
        across = 2 * apothem + gap
        return apothem, across, across * math.sqrt(3) / 2
    half_diag = size / 2
    apothem = half_diag / math.sqrt(2)
    across = 2 * half_diag + gap
    return apothem, across, across / 2


def _shape(wp: cq.Workplane) -> cq.Shape:
    return cast(cq.Shape, wp.val())


def _compound(solids: list[cq.Shape]) -> cq.Compound | None:
    return cq.Compound.makeCompound(solids) if solids else None


def wall_cutters(
    kind: str, radius: float, z0: float, z1: float, size: float, depth: float, gap: float
) -> cq.Compound | None:
    """Cutters for the outside of a cylinder of ``radius`` between heights ``z0`` and ``z1``."""
    if kind == "none":
        return None
    if kind == "flutes":
        rf = size / 2
        n = max(6, round(2 * math.pi * radius / (size + gap)))
        flute = (
            cq.Workplane("XY")
            .workplane(offset=z0)
            .center(radius + rf - depth, 0)
            .circle(rf)
            .extrude(z1 - z0)
        )
        base = _shape(flute)
        return _compound(
            [base.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 360 * i / n) for i in range(n)]
        )
    if kind == "rings":
        solids = []
        pitch = size + gap
        z = z0 + depth + _OUT
        while z + depth + _OUT <= z1:
            prof = [
                (radius + _OUT, z - depth - _OUT),
                (radius - depth, z),
                (radius + _OUT, z + depth + _OUT),
            ]
            ring = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
            solids.append(_shape(ring))
            z += pitch
        return _compound(solids)

    sides = 6 if kind == "hex" else 4
    apothem, across, row_pitch = _lattice(sides, size, gap)
    if apothem <= depth:
        raise ValueError("pattern_depth too deep for pattern_size")
    n = max(6, round(2 * math.pi * radius / across))
    cutter = _shape(_frustum(sides, apothem, depth)).rotate(
        cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), 90
    )
    solids = []
    row = 0
    z = z0 + apothem * (1 if sides == 6 else math.sqrt(2)) + 0.4
    z_top = z1 - (apothem if sides == 6 else apothem * math.sqrt(2)) - 0.4
    while z <= z_top:
        offset = (360 / n) / 2 if row % 2 else 0.0
        for i in range(n):
            ang = 360 * i / n + offset
            solids.append(
                cutter.translate(cq.Vector(radius, 0, z)).rotate(
                    cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), ang
                )
            )
        row += 1
        z += row_pitch
    return _compound(solids)


def face_cutters(
    kind: str, radius: float, size: float, depth: float, gap: float
) -> cq.Compound | None:
    """Cutters recessed into the z=0 face of a disc of ``radius`` (material is z > 0)."""
    if kind == "none":
        return None
    if kind == "rings":
        solids = []
        r = size
        while r + depth + _OUT <= radius:
            prof = [(r - depth - _OUT, -_OUT), (r, depth), (r + depth + _OUT, -_OUT)]
            ring = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
            solids.append(_shape(ring))
            r += size
        return _compound(solids)
    if kind == "rays":
        # Start far enough out that neighbouring cutters (flare included) never overlap.
        width = 2 * (depth + _OUT) + 0.4
        r0 = 9.0
        n = int(2 * math.pi * r0 / max(width, size / 2))
        length = radius - 3.0 - r0
        if n < 6 or length <= 2:
            raise ValueError("lid too small for the rays pattern")
        prof = [(-_OUT - depth, -_OUT), (0, depth), (_OUT + depth, -_OUT)]
        ray = _shape(cq.Workplane("YZ").workplane(offset=r0).polyline(prof).close().extrude(length))
        return _compound(
            [ray.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 360 * i / n) for i in range(n)]
        )
    if kind == "hex":
        apothem, across, row_pitch = _lattice(6, size, gap)
        if apothem <= depth:
            raise ValueError("pattern_depth too deep for pattern_size")
        cutter = _shape(_frustum(6, apothem, depth)).rotate(
            cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180
        )
        solids = []
        reach = radius - 1.2 * apothem
        rows = int(reach / row_pitch)
        for j in range(-rows, rows + 1):
            y = j * row_pitch
            shift = across / 2 if j % 2 else 0.0
            cols = int(reach / across) + 1
            for i in range(-cols, cols + 1):
                x = i * across + shift
                if math.hypot(x, y) <= reach:
                    solids.append(
                        cutter.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90).translate(
                            cq.Vector(x, y, 0)
                        )
                    )
        return _compound(solids)
    raise ValueError(f"unknown face pattern {kind!r}")
