"""Board enclosure: standoffs, port cutouts and a snap-fit lid.

The body prints open end up and the lid prints flat (plate on the bed, lip up); neither
needs supports. The lid lip carries shallow 45-degree bumps that click into matching
grooves in the body wall. Deflection is kept to ``snap`` (0.3 mm) over a tall thin lip
so the strain stays well inside what PLA tolerates.

Board dimensions are data (:data:`BOARDS`), not code. The presets are from memory of the
published drawings and are unverified: measure your board and use ``board="custom"``
(with ``board_length`` etc.) if anything disagrees.

Run directly to export an STL::

    python -m daneel.parts.enclosure --board pi4 --out output/enclosure.stl
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

_PIECES = ("both", "body", "lid")


@dataclass(frozen=True)
class Port:
    """A rectangular opening on a board edge.

    ``edge`` is x0/x1/y0/y1 (board frame, origin at the lower-left corner). ``at`` is the
    centre along the edge, ``z`` the bottom of the opening relative to the board's top
    surface (negative reaches below the board, e.g. an SD slot).
    """

    edge: str
    at: float
    width: float
    height: float
    z: float


@dataclass(frozen=True)
class Board:
    length: float
    width: float
    thickness: float
    holes: tuple[tuple[float, float], ...]
    hole_d: float
    headroom: float  # tallest component above the board top
    ports: tuple[Port, ...] = ()


BOARDS: dict[str, Board] = {
    "pi4": Board(
        85.0,
        56.0,
        1.4,
        ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)),
        2.7,
        17.0,
        (
            Port("x1", 10.25, 16.0, 13.5, 0.0),  # ethernet
            Port("x1", 29.0, 13.5, 16.0, 0.0),  # USB
            Port("x1", 47.0, 13.5, 16.0, 0.0),  # USB
            Port("y0", 11.2, 9.5, 3.6, 0.0),  # USB-C power
            Port("y0", 26.0, 7.8, 3.8, 0.0),  # micro HDMI 0
            Port("y0", 39.5, 7.8, 3.8, 0.0),  # micro HDMI 1
            Port("y0", 53.5, 7.2, 6.2, 0.0),  # audio jack
            Port("x0", 28.0, 12.0, 2.8, -2.8),  # microSD, under the board
        ),
    ),
    "pi_zero": Board(
        65.0,
        30.0,
        1.4,
        ((3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)),
        2.7,
        5.5,
        (
            Port("y0", 12.4, 11.8, 3.8, 0.0),  # mini HDMI
            Port("y0", 41.4, 8.4, 3.2, 0.0),  # micro USB data
            Port("y0", 54.0, 8.4, 3.2, 0.0),  # micro USB power
            Port("x0", 16.9, 12.0, 2.8, -2.8),  # microSD
        ),
    ),
}


@dataclass
class EnclosureParams:
    """Parameters for a board enclosure. All dimensions in millimetres."""

    board: str = "pi4"  # preset name, or "custom"
    board_length: float = 85.0  # custom board only
    board_width: float = 56.0
    board_thickness: float = 1.4
    hole_dx: float = 58.0  # hole spacing, custom board only
    hole_dy: float = 49.0
    hole_inset: float = 3.5
    hole_d: float = 2.7
    headroom: float = 0.0  # extra clearance above the board top; 0 = preset default
    board_clearance: float = 0.6  # gap around the board
    wall: float = 2.0
    floor: float = 2.0
    standoff_height: float = 4.0
    standoff_d: float = 6.0
    lid_thickness: float = 2.0
    lip_height: float = 0.0  # lid lip depth; 0 = auto (8 mm, less if the board is shallow)
    lip_wall: float = 1.6
    fit_gap: float = 0.25  # lip-to-wall clearance
    snap: float = 0.25  # detent depth
    port_margin: float = 0.5  # extra around each port opening
    vent_slots: int = 6  # lid vent slots (0 disables)
    piece: str = "both"  # both | body | lid
    gap: float = 8.0  # spacing between pieces on the bed

    def resolve(self) -> Board:
        if self.board == "custom":
            i = self.hole_inset
            holes = (
                (i, i),
                (i + self.hole_dx, i),
                (i, i + self.hole_dy),
                (i + self.hole_dx, i + self.hole_dy),
            )
            return Board(
                self.board_length,
                self.board_width,
                self.board_thickness,
                holes,
                self.hole_d,
                self.headroom or 10.0,
            )
        if self.board not in BOARDS:
            raise ValueError(
                f"unknown board {self.board!r}; use one of {', '.join(BOARDS)} or custom"
            )
        return BOARDS[self.board]

    def validate(self) -> None:
        if self.piece not in _PIECES:
            raise ValueError(f"piece must be one of {', '.join(_PIECES)}")
        b = self.resolve()
        if min(b.length, b.width, b.thickness) <= 0:
            raise ValueError("board dimensions must be positive")
        for x, y in b.holes:
            if not (0 < x < b.length and 0 < y < b.width):
                raise ValueError("mounting holes must lie on the board")
        if self.wall < 1.6 or self.floor < 1.2 or self.lid_thickness < 1.2:
            raise ValueError("wall >= 1.6, floor and lid_thickness >= 1.2 mm")
        if self.lip_wall < 1.2:
            raise ValueError("lip_wall must be at least 1.2 mm")
        if not 0 <= self.snap <= 0.6:
            raise ValueError("snap must be between 0 and 0.6 mm")
        if self.fit_gap < 0 or self.board_clearance < 0:
            raise ValueError("fit_gap and board_clearance must be non-negative")
        if self.snap + self.fit_gap + 0.4 > self.wall:
            raise ValueError("wall too thin for the snap groove")
        if self.standoff_d <= b.hole_d + 1.2:
            raise ValueError("standoff_d too small for the board hole")
        if self.vent_slots < 0 or self.gap < 0:
            raise ValueError("vent_slots and gap must be non-negative")


def _headroom(p: EnclosureParams, b: Board) -> float:
    return p.headroom if p.headroom > 0 else b.headroom


def _dims(p: EnclosureParams, b: Board) -> tuple[float, float, float, float]:
    """Inner length/width, outer length/width."""
    il = b.length + 2 * p.board_clearance
    iw = b.width + 2 * p.board_clearance
    return il, iw, il + 2 * p.wall, iw + 2 * p.wall


def _lip(p: EnclosureParams, b: Board) -> float:
    """Lip depth: it must stay clear of the board's top surface."""
    room = _body_height(p, b) - (p.floor + p.standoff_height + b.thickness) - 0.5
    lip = p.lip_height if p.lip_height > 0 else min(8.0, room)
    if lip < 4:
        raise ValueError("not enough headroom for the snap lip (needs 4 mm); raise headroom")
    if lip > room:
        raise ValueError(f"lip_height {lip:g} would hit the board; maximum is {room:g}")
    return lip


def _body_height(p: EnclosureParams, b: Board) -> float:
    return p.floor + p.standoff_height + b.thickness + _headroom(p, b) + 1.0


_BUMP_FROM_TIP = 2.5  # detent centre, measured from the lip tip
_CORNER = 3.0  # outer vertical-edge radius


def _ridge(face: float, depth: float, z: float, length: float, rot: float) -> cq.Workplane:
    """45-degree ridge proud of ``face`` (a distance from the centre on +X), rotated about Z."""
    r = depth + 0.4
    pts = [
        (face - 0.2, z - r),
        (face + depth, z - 0.4),
        (face + depth, z + 0.4),
        (face - 0.2, z + r),
    ]
    ridge = cq.Workplane("XZ").polyline(pts).close().extrude(length / 2, both=True)
    return ridge.rotate((0, 0, 0), (0, 0, 1), rot)


def _ridges(
    p: EnclosureParams,
    il: float,
    iw: float,
    face_inset: float,
    depth: float,
    z: float,
    extra: float,
):
    """One ridge per wall, on the +X/-X/+Y/-Y faces, ``face_inset`` inside the cavity wall."""
    out = None
    for rot, half, span in (
        (0, il / 2, iw),
        (180, il / 2, iw),
        (90, iw / 2, il),
        (270, iw / 2, il),
    ):
        length = max(span * 0.35, 10.0) + extra
        r = _ridge(half - face_inset, depth, z, length, rot)
        out = r if out is None else out.union(r)
    return out


def _body(p: EnclosureParams, b: Board) -> cq.Workplane:
    il, iw, ol, ow = _dims(p, b)
    h = _body_height(p, b)
    outer = (
        cq.Workplane("XY").box(ol, ow, h, centered=(True, True, False)).edges("|Z").fillet(_CORNER)
    )
    outer = outer.faces("<Z").edges().chamfer(0.6)
    inner_r = max(_CORNER - p.wall, 0.5)
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=p.floor)
        .box(il, iw, h, centered=(True, True, False))
        .edges("|Z")
        .fillet(inner_r)
    )
    body = outer.cut(cavity)

    ox, oy = -b.length / 2, -b.width / 2
    top = p.floor + p.standoff_height
    for hx, hy in b.holes:
        x, y = ox + hx, oy + hy
        post = (
            cq.Workplane("XY")
            .workplane(offset=p.floor - 0.1)
            .center(x, y)
            .circle(p.standoff_d / 2)
            .extrude(p.standoff_height + 0.1)
        )
        pin = (
            cq.Workplane("XY")
            .workplane(offset=top - 0.1)
            .center(x, y)
            .circle((b.hole_d - 0.25) / 2)
            .extrude(1.3)
        )
        body = body.union(post).union(pin)

    board_top = top + b.thickness
    m = p.port_margin
    for port in b.ports:
        z0 = board_top + port.z - m
        hgt = port.height + 2 * m
        w = port.width + 2 * m
        depth = p.wall + 2.0
        if port.edge in ("x0", "x1"):
            sgn = -1 if port.edge == "x0" else 1
            cx = sgn * (il / 2 + p.wall / 2)
            cy = oy + port.at
            size = (depth, w, hgt)
        else:
            sgn = -1 if port.edge == "y0" else 1
            cx = ox + port.at
            cy = sgn * (iw / 2 + p.wall / 2)
            size = (w, depth, hgt)
        cutter = cq.Workplane("XY").box(*size, centered=(True, True, False)).translate((cx, cy, z0))
        body = body.cut(cutter)

    if p.snap > 0:
        z = h - _lip(p, b) + _BUMP_FROM_TIP
        body = body.cut(_ridges(p, il, iw, 0.0, p.snap + 0.1, z, 1.0))
    return body


def _lid(p: EnclosureParams, b: Board) -> cq.Workplane:
    """Lid in print orientation: plate on the bed, lip pointing up."""
    il, iw, ol, ow = _dims(p, b)
    t = p.lid_thickness
    plate = (
        cq.Workplane("XY").box(ol, ow, t, centered=(True, True, False)).edges("|Z").fillet(_CORNER)
    )
    plate = plate.faces("<Z").edges().chamfer(0.6)
    inner_r = max(_CORNER - p.wall, 0.5)
    lo = max(inner_r - p.fit_gap, 0.5)
    lip_l, lip_w = il - 2 * p.fit_gap, iw - 2 * p.fit_gap
    lip = (
        cq.Workplane("XY")
        .workplane(offset=t - 0.1)
        .box(lip_l, lip_w, _lip(p, b) + 0.1, centered=(True, True, False))
        .edges("|Z")
        .fillet(lo)
    )
    hollow = (
        cq.Workplane("XY")
        .workplane(offset=t - 0.2)
        .box(
            lip_l - 2 * p.lip_wall,
            lip_w - 2 * p.lip_wall,
            _lip(p, b) + 0.4,
            centered=(True, True, False),
        )
        .edges("|Z")
        .fillet(max(lo - p.lip_wall, 0.3))
    )
    lid = plate.union(lip.cut(hollow))
    if p.snap > 0:
        z = t + _lip(p, b) - _BUMP_FROM_TIP
        lid = lid.union(_ridges(p, il, iw, p.fit_gap, p.fit_gap + p.snap, z, 0.0))
    if p.vent_slots:
        pitch = 4.0
        span = (p.vent_slots - 1) * pitch
        for i in range(p.vent_slots):
            slot = (
                cq.Workplane("XY").center(0, -span / 2 + i * pitch).rect(il * 0.5, 2.0).extrude(t)
            )
            lid = lid.cut(slot)
    return lid


def build(params: EnclosureParams | None = None) -> cq.Workplane:
    """Build the enclosure; ``piece`` selects body, lid, or both side by side."""
    p = params or EnclosureParams()
    p.validate()
    b = p.resolve()
    _lip(p, b)
    if p.piece == "body":
        return _body(p, b)
    if p.piece == "lid":
        return _lid(p, b)
    _, _, ol, _ = _dims(p, b)
    body = _body(p, b).translate((-(ol / 2 + p.gap / 2), 0, 0))
    lid = _lid(p, b).translate((ol / 2 + p.gap / 2, 0, 0))
    return cq.Workplane("XY").add(body.vals()).add(lid.vals())


def _main() -> None:
    import argparse

    from daneel.export import export

    ap = argparse.ArgumentParser(description="Generate a board enclosure.")
    for name, default in vars(EnclosureParams()).items():
        ap.add_argument(f"--{name.replace('_', '-')}", type=type(default), default=default)
    ap.add_argument("--out", default="output/enclosure.stl")
    args = vars(ap.parse_args())
    out = args.pop("out")
    print(f"wrote {export(build(EnclosureParams(**args)), out)}")


if __name__ == "__main__":
    _main()
