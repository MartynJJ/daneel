"""Screw-top jar: a cylindrical container and a threaded lid, printed side by side.

Both pieces come from one parameter set, so the lid always matches the body. The body
prints open end up and the lid prints with its flat top on the bed; neither needs
supports. ``clearance`` is the printer-specific fit allowance and is the number to tune
with ``piece="test"`` (a short thread-only pair) before printing a whole jar.

Run directly to export an STL::

    python -m daneel.parts.jar --out output/jar.stl
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

import cadquery as cq

from daneel.parts.threads import helical_solid, trapezoid

_PIECES = ("both", "body", "lid", "test")
_EMBED = 0.3  # thread bases sink this far into the wall so unions share volume


def _volume(wp: cq.Workplane) -> float:
    return float(sum(cast(cq.Solid, s).Volume() for s in wp.solids().vals()))


def _joined(base: cq.Workplane, add: cq.Workplane, what: str) -> cq.Workplane:
    """Union ``add`` onto ``base``, failing loudly if OCC silently drops a solid.

    Plain unions with helical faces can return just one operand; the fuzzy tolerance
    makes them reliable, and the volume check catches any remaining no-op.
    """
    result = base.union(add, tol=1e-4)
    if _volume(result) < _volume(base) + 0.2 * _volume(add):
        raise RuntimeError(f"{what} did not fuse; adjust the parameters slightly")
    return result


@dataclass
class JarParams:
    """Parameters for a screw-top jar. All dimensions in millimetres."""

    outer_d: float = 40.0  # body outer diameter
    height: float = 30.0  # body height, rim to base
    wall: float = 3.0  # body wall; the neck wall is this minus thread_depth
    floor: float = 2.0
    thread_pitch: float = 3.0
    thread_depth: float = 1.2
    thread_height: float = 10.0  # neck length carrying the thread
    clearance: float = 0.3  # radial and flank allowance between thread and lid
    lid_wall: float = 2.0  # lid skirt thickness outside the body diameter
    lid_top: float = 2.5  # lid cap thickness
    grip: int = 24  # vertical grip grooves around the lid (0 disables)
    gap: float = 8.0  # spacing between the two pieces on the bed
    piece: str = "both"  # both | body | lid | test

    def validate(self) -> None:
        if self.piece not in _PIECES:
            raise ValueError(f"piece must be one of {', '.join(_PIECES)}")
        if min(self.outer_d, self.height, self.thread_pitch, self.thread_height) <= 0:
            raise ValueError("diameter, height, pitch and thread_height must be positive")
        if self.thread_depth <= 0 or self.clearance < 0:
            raise ValueError("thread_depth must be positive and clearance non-negative")
        if self.wall - self.thread_depth < 1.2:
            raise ValueError("neck wall (wall - thread_depth) must be at least 1.2 mm")
        if self.thread_height >= self.height - self.floor:
            raise ValueError("thread_height must leave room for the floor")
        if self.thread_height < self.thread_pitch * 1.5:
            raise ValueError("thread_height must cover at least 1.5 pitches")
        if self.thread_pitch * 0.5 - 2 * self.clearance < 0.8:
            raise ValueError("pitch too fine: lid ridge would be thinner than two 0.4 mm lines")
        if self.lid_wall < 1.2 or self.lid_top < 1.2:
            raise ValueError("lid_wall and lid_top must be at least 1.2 mm")
        if self.outer_d / 2 - self.wall <= 3:
            raise ValueError("wall too thick for the diameter")
        if self.grip < 0 or self.gap < 0:
            raise ValueError("grip and gap must be non-negative")


def _thread_dims(p: JarParams) -> tuple[float, float, float, float]:
    """Return (outer radius, neck root radius, root width, crest width) of the body thread."""
    r = p.outer_d / 2
    root_w = p.thread_pitch * 0.5
    crest_w = p.thread_pitch * 0.17
    return r, r - p.thread_depth, root_w, crest_w


def _body(p: JarParams, neck_h: float, total_h: float) -> cq.Workplane:
    r, r_root, root_w, crest_w = _thread_dims(p)
    shoulder = total_h - neck_h
    r_in = r - p.wall
    # Plain geometry first (hollow base + hollow neck tube); the helical solid joins last,
    # because OCC booleans with helical faces are order-sensitive and can silently no-op.
    base = (
        cq.Workplane("XY")
        .circle(r)
        .circle(r_in)
        .extrude(shoulder)
        .union(cq.Workplane("XY").circle(r).extrude(p.floor))
        .faces("<Z")
        .edges()
        .chamfer(0.6)
    )
    tube = (
        cq.Workplane("XY")
        .workplane(offset=shoulder - 0.1)
        .circle(r_root)
        .circle(r_in)
        .extrude(neck_h + 0.1)
    )

    thread = helical_solid(
        trapezoid(root_w + _EMBED, crest_w, -_EMBED, p.thread_depth),
        p.thread_pitch,
        neck_h + 2 * p.thread_pitch,
        r_root,
        z0=shoulder - p.thread_pitch,
    )
    lead = p.thread_depth + 0.8
    envelope = (
        cq.Workplane("XY")
        .workplane(offset=shoulder - 0.05)
        .circle(r + 0.5)
        .extrude(neck_h + 0.05)
        .faces(">Z")
        .edges()
        .chamfer(lead + 0.5)
    )
    threaded = _joined(tube, thread.intersect(envelope), "body thread")
    return _joined(base, threaded, "body neck")


def _lid(p: JarParams, neck_h: float) -> cq.Workplane:
    """Lid in print orientation: flat top on the bed (z=0), opening facing up."""
    r, r_root, root_w, crest_w = _thread_dims(p)
    c = p.clearance
    r_lid = r + p.lid_wall
    depth = neck_h + 0.3
    total = p.lid_top + depth
    lid = cq.Workplane("XY").circle(r_lid).extrude(total)
    lid = lid.faces("<Z").edges().chamfer(0.8)

    if p.grip:
        groove_r = 1.0
        for i in range(p.grip):
            a = 2 * math.pi * i / p.grip
            lid = lid.cut(
                cq.Workplane("XY")
                .center(r_lid * math.cos(a), r_lid * math.sin(a))
                .circle(groove_r)
                .extrude(total)
            )
    # Re-add a thin skin where grooves would otherwise reach the bore.
    bore = cq.Workplane("XY").workplane(offset=p.lid_top).circle(r + c).extrude(depth + 1)
    lid = lid.cut(bore)

    # The ridge fills the body's groove: the body's groove widens from root to crest,
    # so the ridge is the same trapezoid grown to the groove and shrunk by the flank gap.
    groove_root = p.thread_pitch - root_w
    groove_crest = p.thread_pitch - crest_w
    ridge = helical_solid(
        trapezoid(
            groove_crest - 2 * c,
            groove_root - 2 * c,
            _EMBED,
            -(p.thread_depth - c),
        ),
        p.thread_pitch,
        depth + 2 * p.thread_pitch,
        r + c,
        z0=p.lid_top - p.thread_pitch,
    )
    envelope = (
        cq.Workplane("XY")
        .workplane(offset=p.lid_top)
        .circle(r_lid - 0.5)
        .extrude(depth)
        .faces(">Z")
        .edges()
        .chamfer(0.01)
    )
    return _joined(lid, ridge.intersect(envelope), "lid thread")


def build(params: JarParams | None = None) -> cq.Workplane:
    """Build the jar; ``piece`` selects body, lid, both side by side, or the test pair."""
    p = params or JarParams()
    p.validate()
    r = p.outer_d / 2
    r_lid = r + p.lid_wall

    if p.piece == "test":
        neck_h = p.thread_pitch * 2.5
        total_h = p.floor + neck_h + 3.0
        body = _body(p, neck_h, total_h)
        lid = _lid(p, neck_h)
    else:
        body = _body(p, p.thread_height, p.height)
        lid = _lid(p, p.thread_height)

    if p.piece == "body":
        return body
    if p.piece == "lid":
        return lid
    body = body.translate((-(r + p.gap / 2), 0, 0))
    lid = lid.translate((r_lid + p.gap / 2, 0, 0))
    return cq.Workplane("XY").add(body.vals()).add(lid.vals())


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a screw-top jar.")
    for name, default in vars(JarParams()).items():
        kind = type(default)
        ap.add_argument(f"--{name.replace('_', '-')}", type=kind, default=default)
    ap.add_argument("--out", default="output/jar.stl")
    args = vars(ap.parse_args())
    out = args.pop("out")
    print(f"wrote {export(build(JarParams(**args)), out)}")


if __name__ == "__main__":
    _main()
