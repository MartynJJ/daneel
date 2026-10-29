"""Helmet mount for a clip-on light that has a T-shaped post on its back.

The light slides sideways into a T-slot: a wide chamber holds the post's head under a lip, a
narrow slot lets the neck through, and a stop wall at the far end halts it. The post was
measured from photos and one caliper reading, so print ``piece=test`` first: three short
slots at different clearances on one strip; keep the one that slides in snugly.

The plate is flat unless ``helmet_radius`` is set; a curved underside needs supports, so a
thin flexible plate on 1 mm VHB tape is the support-free route.

Run directly to export an STL::

    python -m daneel.parts.light_mount --out output/light_mount.stl
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq


@dataclass
class LightMountParams:
    """Parameters for a T-slot helmet mount. All dimensions in millimetres."""

    head_w: float = 17.0  # post head width, across the slide direction (caliper reading)
    head_l: float = 16.0  # post head length, along the slide direction (estimated)
    head_t: float = 1.8  # post head thickness (estimated)
    neck_w: float = 12.0  # widest dimension of the post's neck (estimated)
    neck_h: float = 3.3  # light back to underside of the head (estimated)
    clearance: float = 0.3  # per side, head chamber and neck slot
    z_clearance: float = 0.3  # vertical play of the head in its chamber
    wall: float = 2.0  # side walls and stop wall
    block_l: float = 25.0
    tab_w: float = 20.0  # flat wing each side of the block, for tape
    plate_t: float = 1.6
    corner_r: float = 4.0
    helmet_radius: float = (
        0.0  # 0 = flat; else underside curved across the tabs (edges-only bed contact)
    )
    piece: str = "mount"  # mount | test
    test_step: float = 0.15  # clearance difference between the test slots

    def validate(self) -> None:
        if self.piece not in ("mount", "test"):
            raise ValueError("piece must be 'mount' or 'test'")
        if min(self.head_w, self.head_l, self.head_t, self.neck_w, self.neck_h) <= 0:
            raise ValueError("post dimensions must be positive")
        if self.neck_w >= self.head_w - 2:
            raise ValueError("neck_w must be at least 2 mm narrower than head_w")
        if self.neck_h <= self.z_clearance + 1.0:
            raise ValueError("neck_h must exceed z_clearance by at least 1 mm (lip thickness)")
        if not 0.05 <= self.clearance <= 0.8 or not 0 <= self.z_clearance <= 0.8:
            raise ValueError("clearance 0.05-0.8 mm, z_clearance 0-0.8 mm")
        if self.wall < 1.2:
            raise ValueError("wall must be at least 1.2 mm")
        if self.block_l < self.head_l + self.wall + 2:
            raise ValueError("block_l too short for the head plus the stop wall")
        if self.plate_t < 1.2:
            raise ValueError("plate_t must be at least 1.2 mm")
        if self.tab_w < 3:
            raise ValueError("tab_w must be at least 3 mm")
        if self.corner_r * 2 >= self.block_l:
            raise ValueError("corner_r too large")
        if self.helmet_radius and self.helmet_radius < 1.5 * self._block_w() / 2 + 1.5 * self.tab_w:
            raise ValueError(
                "helmet_radius is too tight for the tab span; use 0 or a larger radius"
            )
        if self.test_step <= 0 or self.clearance - self.test_step < 0.05:
            raise ValueError("test_step must be positive and leave the tightest slot >= 0.05 mm")

    def _block_w(self, clearance: float | None = None) -> float:
        c = self.clearance if clearance is None else clearance
        return self.head_w + 2 * c + 2 * self.wall

    def sag(self, width: float) -> float:
        """Drop of the curved underside at the tab edges; the top is raised by this much."""
        if not self.helmet_radius:
            return 0.0
        r, half = self.helmet_radius, width / 2
        return r - math.sqrt(r * r - half * half)

    def top(self, width: float) -> float:
        return self.plate_t + self.sag(width)

    def lip_t(self) -> float:
        return self.neck_h - self.z_clearance

    def chamber_h(self) -> float:
        return self.head_t + self.z_clearance

    def block_h(self) -> float:
        return self.chamber_h() + self.lip_t()


def _slot_block(
    p: LightMountParams, clearance: float, x0: float, y0: float, z0: float
) -> cq.Workplane:
    """Block with a T-slot open at its -X end, standing on the plate (z from plate_t)."""
    bw = p._block_w(clearance)
    bl = p.block_l
    blk = cq.Workplane("XY").workplane(offset=z0).center(x0, y0).rect(bl, bw).extrude(p.block_h())
    cut_l = bl - p.wall + 1.0  # runs out through the open end, stops at the stop wall
    cx = x0 - bl / 2 + cut_l / 2 - 1.0
    chamber = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(cx, y0)
        .rect(cut_l, p.head_w + 2 * clearance)
        .extrude(p.chamber_h())
    )
    slot = (
        cq.Workplane("XY")
        .workplane(offset=z0 + p.chamber_h() - 0.01)
        .center(cx, y0)
        .rect(cut_l, p.neck_w + 2 * clearance)
        .extrude(p.lip_t() + 0.02)
    )
    return blk.cut(chamber).cut(slot)


def _plate(p: LightMountParams, length: float, width: float) -> cq.Workplane:
    top = p.top(width)
    plate = (
        cq.Workplane("XY")
        .rect(length, width)
        .extrude(top)
        .edges("|Z")
        .fillet(min(p.corner_r, width / 2 - 0.1, length / 2 - 0.1))
    )
    if p.helmet_radius:
        r = p.helmet_radius
        helmet = (
            cq.Workplane("YZ")
            .workplane(offset=-length / 2 - 1)
            .circle(r)
            .extrude(length + 2)
            .translate((0, 0, p.sag(width) - r))
        )
        plate = plate.cut(helmet)
    return plate


def build(params: LightMountParams) -> cq.Workplane:
    params.validate()
    p = params
    plate_l = p.block_l + 8
    if p.piece == "test":
        clearances = [p.clearance - p.test_step, p.clearance, p.clearance + p.test_step]
        pitch = p._block_w(max(clearances)) + 3
        width = pitch * 3 + 3
        plate = _plate(p, plate_l, width)
        for i, c in enumerate(clearances):
            plate = plate.union(_slot_block(p, c, 0, (i - 1) * pitch, p.top(width)))
        return plate
    width = p._block_w() + 2 * p.tab_w
    return _plate(p, plate_l, width).union(_slot_block(p, p.clearance, 0, 0, p.top(width)))


if __name__ == "__main__":
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output/light_mount.stl")
    args = ap.parse_args()
    print(export(build(LightMountParams()), args.out))
