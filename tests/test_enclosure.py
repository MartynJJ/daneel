"""Tests for the board enclosure (geometry, snap fit, board clearance)."""

import dataclasses

import pytest

cq = pytest.importorskip("cadquery")

from daneel.parts.enclosure import BOARDS, EnclosureParams, _body_height, build  # noqa: E402


def _fit(board: str):
    p = EnclosureParams(board=board)
    b = BOARDS[board]
    body = build(EnclosureParams(board=board, piece="body")).val()
    lid = build(EnclosureParams(board=board, piece="lid")).val()
    seated = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate(
        (0, 0, _body_height(p, b) + p.lid_thickness)
    )
    slab = (
        cq.Workplane("XY")
        .workplane(offset=p.floor + p.standoff_height)
        .box(b.length, b.width, b.thickness, centered=(True, True, False))
    )
    for hx, hy in b.holes:
        slab = slab.cut(
            cq.Workplane("XY")
            .workplane(offset=p.floor)
            .center(-b.length / 2 + hx, -b.width / 2 + hy)
            .circle(b.hole_d / 2)
            .extrude(p.standoff_height + 3)
        )
    return body, seated, slab.val()


def _overlap(a, b):
    return a.intersect(b, tol=1e-4).Volume()


def test_validation():
    with pytest.raises(ValueError, match="unknown board"):
        EnclosureParams(board="nope").validate()
    with pytest.raises(ValueError, match="wall"):
        EnclosureParams(wall=1.0).validate()
    with pytest.raises(ValueError, match="piece"):
        EnclosureParams(piece="x").validate()
    with pytest.raises(ValueError, match="hit the board"):
        build(EnclosureParams(board="pi_zero", lip_height=9.0))


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_pieces_valid_and_lid_seats(board):
    body, seated, slab = _fit(board)
    assert body.isValid() and seated.isValid()
    assert _overlap(body, seated) == pytest.approx(0, abs=0.01)
    assert _overlap(body, seated.translate((0, 0, 0.3))) > 1  # detent holds the lid down
    assert _overlap(body, seated.translate((0, 0, -0.5))) > 50  # hard stop on the rim


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_board_clears_walls_lid_and_pins(board):
    body, seated, slab = _fit(board)
    assert _overlap(slab, body) == pytest.approx(0, abs=0.01)
    assert _overlap(slab, seated) == pytest.approx(0, abs=0.01)


def test_ports_are_cut_through_the_wall(monkeypatch):
    ported = build(EnclosureParams(piece="body")).val().Volume()
    monkeypatch.setitem(BOARDS, "bare", dataclasses.replace(BOARDS["pi4"], ports=()))
    bare = build(EnclosureParams(board="bare", piece="body")).val().Volume()
    assert bare - ported > 500


def test_both_pieces_laid_out_side_by_side():
    assert len(build(EnclosureParams()).solids().vals()) == 2
