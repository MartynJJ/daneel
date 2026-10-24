# LEGO System (stud/tube bricks) - dimensional specs

All mm. Researched 2026-10-24. Confidence tags: **primary** (patent / maker document), **derived** (computed from a primary artefact, e.g. LDraw 1 LDU = 0.4 mm), **community** (blog, forum, open-source CAD code, listings), **unverified** (single weak source or contradictory), **not found**.

Caveat on LDraw: the LDraw spec itself calls its LDU conversions "approximations" (https://www.ldraw.org/article/218.html). R. Cailliau compares LDraw to measured parts: stud height LDraw 1.6 vs real 1.8; Technic bearing-hole height LDraw 5.6 vs real 5.8 (https://www.cailliau.org/Alphabetical/L/Lego/Dimensions/More%20Dimensions/BBEditPreviewTemp.html). Prefer measured values over LDraw where they differ.

No expired LEGO patent read gives numeric mm/inch dimensions (US 3,005,282, US 3,162,973, US 3,597,875, US 6,461,215 all checked via patents.google.com; only ratios and relationships). So "primary" below means qualitative patent statements; numeric values come from LDraw (derived) and community measurements.

## Grid, stud, heights

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Stud pitch | 8.0 (20 LDU) | derived | https://www.ldraw.org/article/218.html |
| Stud pitch, measured | 7.985-7.986 (+-0.002 at 25 C), from late-1990s Technic beams | community (R. Munafo via LUGNET) | https://www.lugnet.com/~330/FAQ/Build/dimensions |
| Stud diameter | 4.8 (12 LDU) | derived | https://www.ldraw.org/article/218.html |
| Stud diameter, measured | 4.8-4.9, 4.9 preferred | community (Cailliau) | cailliau.org URL above |
| Stud diameter, other | 5.0 (Poskanzer, "approximate") | community | https://www.lugnet.com/~330/FAQ/Build/dimensions |
| Stud height | 1.6 (4 LDU) | derived | ldraw.org/article/218.html |
| Stud height, measured | 1.8 (1.9 over embossed text) | community (Cailliau) | cailliau.org URL above |
| Stud height, other | 1.7 (Poskanzer), 1.8 (OpenSCADLEGO, cfinke) | community | lugnet URL; https://github.com/anandamous/OpenSCADLEGO ; https://github.com/cfinke/LEGO.scad |
| Brick height | 9.6 (24 LDU); 9.582 from Munafo's pitch x 6/5 | derived / community | ldraw.org/article/218.html ; lugnet URL |
| Plate height | 3.2 (8 LDU); 3.194 (Munafo) | derived / community | same |
| Brick = 3 plates | yes | primary-ish (BrickLink help) | https://www.bricklink.com/help.asp?helpID=261 |
| Unit system | 1.6 mm unit; 5 units = 8 mm module, wall/ceiling/stud height 1 unit, stud dia 3 units | community | https://notebook.zoeblade.com/Lego_brick_dimensions.html |
| Outer length/width | n x 8 - 0.2 (0.1 clearance per side) | community (Cailliau; Zoe Blade agrees) | cailliau.org URL ; notebook.zoeblade.com URL |
| Bearing-brick face spacing | 4 x 8 + 0.2 | community (Cailliau) | cailliau.org URL |

## Underside

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Wall thickness | 1.6 (LDraw box 40 outer / 36 inner LDU) | derived | LDraw parts/s/3001s01.dat in https://library.ldraw.org/library/updates/complete.zip |
| Wall thickness, other | 1.5 (Poskanzer, from (pitch - stud dia)/2); 1.45 (OpenSCADLEGO print choice); 1.2 (cfinke, brickify print choices) | community | lugnet URL ; OpenSCADLEGO ; cfinke ; https://github.com/richfelker/brickify |
| Top plate (ceiling) thickness | 1.6 (4 LDU, 3001s01.dat ceiling at y=4) | derived | LDraw complete.zip, parts/s/3001s01.dat |
| Top plate, other | 1.6 (Zoe Blade); 1.0 (OpenSCADLEGO, brickify, cfinke print choices) | community | notebook.zoeblade.com URL ; repos above |
| Tube OD | 6.4 (16 LDU, p/stud4.dat) | derived | LDraw complete.zip |
| Tube OD, other | 6.31 (Poskanzer, sqrt2 x pitch - stud dia); 6.46 (brickify formula); 6.5 (OpenSCADLEGO); 6.6 (diyhpl "#what?", marked uncertain by its author) | community / unverified (6.6) | lugnet URL ; brickify ; OpenSCADLEGO ; https://secure.diyhpl.us/cgit/lego/plain/dimensions.yaml |
| Tube ID | 4.8 (12 LDU) | derived | LDraw p/stud4.dat |
| Tube ID, qualitative | "inside diameter of the tubular projection equals the diameter of the cylindrical projections" (stud dia) | primary | US 3,005,282 claim 2, https://patents.google.com/patent/US3005282A/en |
| Tube wall | 0.657 (Poskanzer); 0.85 (OpenSCADLEGO print choice); 0.8 (derived from LDraw 6.4 OD / 4.8 ID) | community / derived | lugnet URL ; OpenSCADLEGO |
| Tube placement | centred between four studs (grid intersections at half-pitch offset), i.e. 4 mm from brick edge for 2xN | derived | LDraw 3001s01.dat (stud4 at x=0,+-20 LDU between stud rows at z=+-10) |
| Tube length | full cavity depth, ceiling to open bottom (LDraw 20 LDU = 8.0 mm) | derived | LDraw 3001s01.dat |
| 1xN brick centre pin | 3.0-3.18 dia (print designs; real element not verified) | community | OpenSCADLEGO (3) ; cfinke (3.18) |
| Plate wall depth | 2.25 | unverified | diyhpl yaml URL |

## Tolerances and clutch

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Mould tolerance | < 0.01 (possibly ~0.005) | community (Cailliau estimate) | cailliau.org URL |
| Clutch mechanism | "tangential contact" of studs with tube and walls; no interference amount stated | primary (qualitative) | US 3,005,282, https://patents.google.com/patent/US3005282A/en |
| Stud-to-post clearance used in a clutch-tuned CAD | 0.03 per side (stud_play), 0.1 between walls (wall_play) | community | https://github.com/cfinke/LEGO.scad |
| Clutch force (N) / interference (mm) | not found | - | - |

## Printing notes (sourced, all community)

| Note | Source |
|---|---|
| Stud dia 4.85 (vs 4.8), fit tolerance 0.1 subtracted from outer length/width, stud_rescale 1.05, PLA on QIDI Q1 Pro: "clicks in smoothly without losing clutch" | https://github.com/anandamous/OpenSCADLEGO |
| stud_fudge 0.2 added to stud dia, wall_clearance 0.1, stud 4.85 | https://github.com/richfelker/brickify |
| stud_rescale used by owners: 1.03 (Ender 3 Pro, PLA), 1.0475 (Orion Delta, T-Glase), 1.022 (Orion Delta, ABS) | https://github.com/cfinke/LEGO.scad (comments in LEGO.scad) |
| Outer walls reduced 0.1 per side so adjacent bricks do not bind | cfinke ; OpenSCADLEGO ; Cailliau |

## Not found / not read

- Official LEGO group dimension drawings: not found.
- brickfact.com, eurobricks.com (topic 75308), printables.com listings returned HTTP 403; only search-snippet claims seen, not used above.
