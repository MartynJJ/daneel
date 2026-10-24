"""Helical thread geometry for printable screw fits.

CadQuery has no thread primitive, so a thread is a trapezoid profile swept along a
helix. Profiles are kept shallow (flank under 45 degrees from the radial plane) so
the thread prints without supports with its axis vertical.
"""

from __future__ import annotations

import cadquery as cq


def helical_solid(
    profile: list[tuple[float, float]],
    pitch: float,
    length: float,
    radius: float,
    z0: float = 0.0,
) -> cq.Workplane:
    """Sweep ``profile`` along a right-handed helix.

    ``profile`` holds (radial offset from ``radius``, axial offset) points of a closed
    polygon. The helix starts at angle 0 at height ``z0`` and rises ``length``.
    """
    helix = cq.Wire.makeHelix(pitch, length, radius)
    pts = [(radius + dx, dz) for dx, dz in profile]
    prof = cq.Workplane("XZ").polyline(pts).close()
    solid = prof.sweep(cq.Workplane("XY").add(helix), isFrenet=True)
    return solid.translate((0, 0, z0))


def trapezoid(root_w: float, tip_w: float, root_dx: float, tip_dx: float):
    """Symmetric trapezoid from ``root_dx`` (width ``root_w``) to ``tip_dx`` (``tip_w``)."""
    return [
        (root_dx, -root_w / 2),
        (tip_dx, -tip_w / 2),
        (tip_dx, tip_w / 2),
        (root_dx, root_w / 2),
    ]
