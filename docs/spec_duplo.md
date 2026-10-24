# Duplo - dimensional specs

All mm. Researched 2026-10-24. Tags: **primary**, **derived** (LDraw 1 LDU = 0.4 mm from https://library.ldraw.org/library/updates/complete.zip), **community**, **unverified**, **not found**.

Primary source: Interlego's Duplo patent US 3,597,875 (filed 1967-11-29, granted 1971-08-10), https://patents.google.com/patent/US3597875A/en. It gives ratios, no mm/inch figures (OCR garbled in places).

## Dimensions

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Module relative to LEGO | 2x ("module ... twice the basic module"); proportion series "1:2:4" garbled in OCR | primary | US 3,597,875 |
| Stud pitch | 16.0 (40 LDU) | derived | LDraw parts/3011.dat, s/3011s01.dat |
| Stud pitch, other | 16 (brickify, cfinke, EduTechWiki) | community | https://github.com/richfelker/brickify ; https://github.com/cfinke/LEGO.scad ; https://EduTechWiki.unige.ch/en/Doblo_factory |
| Brick height | 19.2 (48 LDU); half-height piece 9.6 | derived / community | LDraw 3011s01.dat ; EduTechWiki |
| Brick height, other | 19.2 (brickify 6 x 3.2) | community | brickify |
| Stud outer diameter | 9.6 (24 LDU, p/stud7.dat) | derived | LDraw |
| Stud outer diameter, other | 9.35 (brickify); 9.40 (cfinke); 9.55 effective with 0.2 fudge | community | brickify ; cfinke |
| Stud inner diameter (hollow) | 7.2 (18 LDU) | derived | LDraw stud7.dat |
| Stud inner, other | 7.35 (brickify); 6.5 (cfinke) | community | same |
| Stud wall | 1.4 ("measured") | community | cfinke LEGO.scad comment |
| Stud height | 1.6 (4 LDU) | derived | LDraw stud7.dat |
| Stud height, other | 4.4 (brickify); 4.5 (cfinke) | community | same. Sources disagree strongly: LDraw is likely wrong here; no measured primary value found |
| Outer wall thickness | 1.6 (outer 80 / inner 76 LDU) | derived | LDraw s/3011s01.dat |
| Wall, other | 1.6 with splines (cfinke); 1.2 (brickify print default) | community | same |
| Underside tube OD | 12.8 (stud8.dat outer radius 16 LDU) | derived | LDraw p/stud8.dat |
| Tube OD, other | 13.1 (cfinke post_diameter); ~13.28 (brickify, sqrt2 x pitch - stud dia) | community | same |
| Tube ID | 11.2 (radius 14 LDU) ; ~11.28 (brickify) | derived / community | LDraw stud8.dat ; brickify |
| Tube wall | 1.0 (cfinke, brickify post_thickness) | community | same |
| Internal cross / splines | thickness 1.0 (brickify spline_thickness) ; 1.0 (cfinke) | community | same. Real cross dimensions: not found |
| Horizontal hole / axle (Duplo) | axle dia 7.25, spline width 3.10 (cfinke, "based on Early Simple Machines Set 9656") | community | cfinke LEGO.scad |
| Clearance parameters | stud clearance 0.4, hole height = stud height + 0.4 | community | brickify |
| Tolerances (measured) | not found | - | - |

## Mating with LEGO

| Statement | Confidence | Source |
|---|---|---|
| Larger element has an even number (>=4) of hollow primary studs; the smaller element's secondary projection is "so dimensioned as to engage four primary studs" (claim 1) | primary | US 3,597,875 |
| Duplo 2:1 scale means a LEGO stud pair pitch (8) x2 = 16; LEGO 4.8 stud (and 3.2 pin) sit inside hollow Duplo studs of inner dia ~7.2 / ~6.5-7.35 (loose / press-fit depends on print) | derived | arithmetic from rows above |
| LEGO tubes fit hollow Duplo studs as an integrated system, patented 1971 | unverified (search snippet of smithsonianmag.com article, not opened) | https://www.smithsonianmag.com/innovation/how-lego-patents-helped-build-toy-empire-brick-by-brick-180971429 |
| cfinke LEGO.scad hollow-stud inner dia for LEGO bricks = 3.18 + 0.02 to press-fit a 3.18 mm bar | community | https://github.com/cfinke/LEGO.scad |

## Printing notes (community)

- cfinke recommends reinforcement (use_reinforcement) for Duplo bricks on FDM: https://github.com/cfinke/LEGO.scad
- brickify supports `std="duplo"` with same wall_clearance 0.1 and stud_fudge 0.2 as LEGO: https://github.com/richfelker/brickify

## Not found

- Any primary mm-dimension source for Duplo: not found.
- Duplo stud height reliable value: conflicting (1.6 vs 4.4-4.5).
- Duplo Technic-style axle hole sizes other than cfinke's: not found.
