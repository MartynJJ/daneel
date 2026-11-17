"""Heat-set insert test coupon.

A flat plate with one row per metric size (M3-M6) and ``steps`` blind holes per row at
increasing diameters. Each hole is engraved with its diameter. Install an insert in each
with a soldering iron, then pick the diameter that seats flush and resists pulling out
or spinning (try the screw and a torque test).

Hole diameters are guesses until the coupon is printed: the defaults bracket the usual
range for a 0.4 mm nozzle (``start`` = guess - step, so the middle column is the guess).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cadquery as cq

# Starting guesses for hole diameter (mm) per size.
GUESS = {"M3": 4.2, "M4": 5.6, "M5": 6.6, "M6": 8.0}
# Typical insert lengths (mm) per size.
LENGTH = {"M3": 5.7, "M4": 8.0, "M5": 9.5, "M6": 12.7}


@dataclass
class InsertCouponParams:
    """Parameters for the insert coupon. All dimensions in millimetres."""

    sizes: tuple[str, ...] = field(default=("M3", "M4", "M5", "M6"))
    steps: int = 3
    step: float = 0.2  # diameter increment between holes in a row
    margin: float = 3.0  # wall between holes and to the plate edge
    floor: float = 2.0  # solid material under each hole
    label: bool = True

    def validate(self) -> None:
        if not self.sizes:
            raise ValueError("sizes cannot be empty")
        for s in self.sizes:
            if s not in GUESS:
                raise ValueError(f"unknown size {s!r}; choose from {', '.join(GUESS)}")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")
        if self.step <= 0:
            raise ValueError("step must be positive")
        if self.margin < 1.5:
            raise ValueError("margin must be >= 1.5")
        if self.floor < 1.0:
            raise ValueError("floor must be >= 1.0")

    def diameters(self, size: str) -> list[float]:
        """Hole diameters for a row, centred on the guess."""
        mid = (self.steps - 1) / 2
        return [round(GUESS[size] + (i - mid) * self.step, 2) for i in range(self.steps)]

    def depth(self, size: str) -> float:
        return LENGTH[size] + 1.0  # room for the insert plus a little melt overflow


def build(params: InsertCouponParams | None = None) -> cq.Workplane:
    """Build the coupon: plate on the bed, holes open on top, labels engraved on top."""
    p = params or InsertCouponParams()
    p.validate()

    row_d = [max(p.diameters(s)) for s in p.sizes]
    pitch_x = [max(p.diameters(s)) + p.margin for s in p.sizes]
    max_pitch = max(pitch_x)
    label_h = 4.0 if p.label else 0.0

    width = p.steps * max_pitch + p.margin
    # Rows run along -Y; each row is as tall as its hole + margin (+ label strip).
    row_h = [d + p.margin + label_h for d in row_d]
    height = sum(row_h) + p.margin
    thick = max(p.depth(s) for s in p.sizes) + p.floor

    plate = cq.Workplane("XY").box(width, height, thick, centered=(False, False, False))

    y = height - p.margin
    for size, rh, rd in zip(p.sizes, row_h, row_d):
        cy = y - rd / 2 - label_h
        for i, d in enumerate(p.diameters(size)):
            cx = p.margin + max_pitch / 2 + i * max_pitch
            hole = (
                cq.Workplane("XY")
                .workplane(offset=thick - p.depth(size))
                .center(cx, cy)
                .circle(d / 2)
                .extrude(p.depth(size) + 1)
            )
            plate = plate.cut(hole)
            if p.label:
                txt = (
                    cq.Workplane("XY")
                    .workplane(offset=thick - 0.4)
                    .center(cx, cy + rd / 2 + label_h / 2 + 0.2)
                    .text(f"{size} {d:.1f}", 2.2, 0.8, combine=False)
                )
                plate = plate.cut(txt)
        y -= rh
    return plate
