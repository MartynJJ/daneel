"""Helmet mount for a clip-on bike light: a thin glue-down plate carrying the clip block.

The light's own strap mount was not measured, so the block is sized from an estimate of the
light's square recess (``slot_w``). Print ``piece=test`` first: three blocks a little under,
at, and over the estimate on one strip; the one that slides in with a click tells you the
real ``slot_w``. The plate is flat unless ``helmet_radius`` is set; a curved underside needs
supports, so a thin flexible plate on 1 mm VHB tape is the support-free route.

Run directly to export an STL::

    python -m daneel.parts.light_mount --out output/light_mount.stl
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq


@dataclass
class LightMountParams:
    """Parameters for a light-clip helmet mount. All dimensions in millimetres."""

    slot_w: float = 11.0  # estimated width of the recess on the light's back
    clearance: float = 0.25  # total per-side slack between block and recess
    block_l: float = 16.0
    block_h: float = 3.0
    bump_d: float = 2.4  # click bumps on the block's top face
    bump_h: float = 0.8
    bump_gap: float = 7.0  # bump centre spacing along the block
    plate_l: float = 40.0
    plate_w: float = 26.0
    plate_t: float = 1.6
    corner_r: float = 4.0
    helmet_radius: float = 0.0  # 0 = flat; else concave spherical underside
    piece: str = "mount"  # mount | test
    test_step: float = 0.4  # width difference between the test blocks

    def validate(self) -> None:
        if self.piece not in ("mount", "test"):
            raise ValueError("piece must be 'mount' or 'test'")
        if self.slot_w < 6 or self.block_l < 8 or self.block_h < 1.5:
            raise ValueError("slot_w >= 6, block_l >= 8, block_h >= 1.5")
        if not 0 <= self.clearance <= 0.8:
            raise ValueError("clearance must be between 0 and 0.8 mm")
        if self.bump_d + 1 > self.slot_w - 2 * self.clearance or self.bump_h >= self.block_h:
            raise ValueError("bumps must fit on the block face and be lower than the block")
        if self.bump_gap + self.bump_d > self.block_l - 3:
            raise ValueError("bumps do not fit along block_l")
        if self.plate_t < 1.2:
            raise ValueError("plate_t must be at least 1.2 mm")
        if self.plate_w < self.slot_w + 8 or self.plate_l < self.block_l + 8:
            raise ValueError("plate must overhang the block by at least 4 mm each side")
        if self.corner_r * 2 >= min(self.plate_w, self.plate_l):
            raise ValueError("corner_r too large")
        if self.helmet_radius and self.helmet_radius < 60:
            raise ValueError("helmet_radius must be 0 (flat) or at least 60 mm")
        if self.test_step <= 0:
            raise ValueError("test_step must be positive")


def _block(p: LightMountParams, width: float, x: float, y: float) -> cq.Workplane:
    """Click block on top of the plate (z from plate_t), lead-in chamfer on its -X end."""
    z0 = p.plate_t
    blk = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(x, y)
        .rect(p.block_l, width)
        .extrude(p.block_h)
        .faces("<X")
        .edges(">Z")
        .chamfer(min(0.8, p.block_h / 2 - 0.1))
    )
    for sx in (-1, 1):
        bump = (
            cq.Workplane("XY")
            .sphere(p.bump_d / 2)
            .translate((x + sx * p.bump_gap / 2, y, z0 + p.block_h - p.bump_d / 2 + p.bump_h))
        )
        blk = blk.union(bump)
    return blk


def _plate(p: LightMountParams, length: float, width: float) -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(length, width)
        .extrude(p.plate_t)
        .edges("|Z")
        .fillet(min(p.corner_r, width / 2 - 0.1))
    )
    if p.helmet_radius:
        r = p.helmet_radius
        reach = math.hypot(length, width) / 2
        sag = r - math.sqrt(r * r - reach * reach)
        if p.plate_t - sag < 1.2:
            raise ValueError(f"plate_t must be at least {sag + 1.2:.1f} mm for this helmet_radius")
        helmet = cq.Workplane("XY").sphere(r).translate((0, 0, sag - r))
        plate = plate.cut(helmet)
    return plate


def build(params: LightMountParams) -> cq.Workplane:
    params.validate()
    p = params
    w = p.slot_w - 2 * p.clearance
    if p.piece == "test":
        widths = [w - p.test_step, w, w + p.test_step]
        pitch = max(widths) + 5
        length = p.block_l + 8
        plate = _plate(p, length, pitch * 3 + 2)
        for i, bw in enumerate(widths):
            plate = plate.union(_block(p, bw, 0, (i - 1) * pitch))
        return plate
    return _plate(p, p.plate_l, p.plate_w).union(_block(p, w, 0, 0))


if __name__ == "__main__":
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output/light_mount.stl")
    args = ap.parse_args()
    print(export(build(LightMountParams()), args.out))
