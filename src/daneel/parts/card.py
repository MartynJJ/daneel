"""Parametric labelled card / tag.

A flat rounded rectangle with embossed (raised) or debossed (recessed) text and an
optional hanging hole — the "hello world" of the Daneel part library. Handy for cable
labels, drawer tags, keychain fobs, or index cards.

Run directly to export an STL::

    python -m daneel.parts.card --text "A-17" --out output/card.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq


@dataclass
class CardParams:
    """Parameters for a labelled card. All dimensions in millimetres."""

    text: str = "DANEEL"
    width: float = 60.0
    height: float = 30.0
    thickness: float = 2.0
    corner_radius: float = 3.0
    font_size: float = 8.0
    text_depth: float = 0.6
    emboss: bool = True  # True = raised text, False = recessed
    hole: bool = True  # punch a hanging hole
    hole_diameter: float = 4.0

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.thickness <= 0:
            raise ValueError("width, height and thickness must be positive")
        if self.corner_radius * 2 >= min(self.width, self.height):
            raise ValueError("corner_radius too large for card size")
        if not self.emboss and self.text_depth >= self.thickness:
            raise ValueError("recessed text_depth must be less than thickness")


def build(params: CardParams | None = None) -> cq.Workplane:
    """Build the card and return a CadQuery Workplane."""
    p = params or CardParams()
    p.validate()

    card = (
        cq.Workplane("XY")
        .box(p.width, p.height, p.thickness, centered=(True, True, False))
        .edges("|Z")
        .fillet(p.corner_radius)
    )

    if p.hole:
        hole_x = -p.width / 2 + p.hole_diameter
        card = card.faces(">Z").workplane().center(hole_x, 0).hole(p.hole_diameter)

    if p.text:
        text_solid = (
            cq.Workplane("XY")
            .workplane(offset=p.thickness)
            .text(
                p.text,
                fontsize=p.font_size,
                distance=p.text_depth if p.emboss else -p.text_depth,
            )
        )
        card = card.union(text_solid) if p.emboss else card.cut(text_solid)

    return card


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a parametric labelled card.")
    ap.add_argument("--text", default="DANEEL")
    ap.add_argument("--width", type=float, default=60.0)
    ap.add_argument("--height", type=float, default=30.0)
    ap.add_argument("--thickness", type=float, default=2.0)
    ap.add_argument("--font-size", type=float, default=8.0)
    ap.add_argument("--no-emboss", action="store_true", help="recess text instead of raising it")
    ap.add_argument("--no-hole", action="store_true")
    ap.add_argument("--out", default="output/card.stl")
    args = ap.parse_args()

    params = CardParams(
        text=args.text,
        width=args.width,
        height=args.height,
        thickness=args.thickness,
        font_size=args.font_size,
        emboss=not args.no_emboss,
        hole=not args.no_hole,
    )
    path = export(build(params), args.out)
    print(f"wrote {path}")


if __name__ == "__main__":
    _main()
