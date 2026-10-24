# Brio wooden railway - dimensional specs

All mm. Researched 2026-10-24. Tags: **primary** (Brio / manufacturer document), **derived**, **community**, **unverified**, **not found**.

No official Brio dimensional document was found. All figures below are community measurements. Guide author notes Brio publishes inch figures rounded to the nearest quarter inch, so metric measurement is the reference.

Sources:
- G = https://woodenrailway.info/track/brio-track-guide (community)
- D = https://github.com/dotscad/trains/blob/master/tracklib.scad (OpenSCAD, constants `wood_*`; community, LGPL / CC-BY-SA)

## Track section

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Width | 40 | community | G ; D `wood_width` 40 |
| Height | 12 | community | G ; D `wood_height` 12 |
| Groove width | 6 | community | G |
| Groove width, other | 5.7 | community | D `wood_well_width` |
| Groove depth | 3 | community | G ; D (12 - well_height 9 = 3) |
| Groove edge-to-edge gap | 20 | community | G |
| Groove edge gap, other | 19.25 | community | D `wood_well_spacing` |
| Groove centre-to-centre | 26 | community | G |
| Groove centre-to-centre, other | ~24.95 (5.7 + 19.25) | derived from D | D |
| Double-track centre spacing | 46 | community | G |
| Short piece length used in OpenSCAD | 53.5 | community | D comment "standard short wooden length" |

## Connectors

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Male peg diameter | 11.5 | community | G |
| Male peg diameter, other | 12.0 (plug radius 6) | community | D `wood_plug_radius` |
| Peg neck length | 7 | community | G |
| Peg neck length, other | 12 (edge to peg centre, i.e. 6 + 12 = 18 total protrusion) | community | D `wood_plug_neck_length` |
| Peg total protrusion | 18.5 (7 + 11.5) vs 18 (D) | derived | G ; D |
| Peg neck width | 6 | community | D `post_w` |
| Female socket diameter | 15-17 | community | G |
| Female socket, other | 12.6 (plug radius + 0.3 cutout, "recommended 0.3-0.8 larger") | community (print design) | D `wood_cutout` |
| Socket throat | 5 long | community | G |
| Socket throat width | 7.5 | community | D `plug_cutout` (cube 7.5 wide) |
| Socket depth (hole depth into track) | not found as a stated figure; G's "5 throat" + 15-17 bore implies ~20-22 from face, D implies 12 + 6.3 = 18.3 | unverified (derived) | G ; D |
| Socket depth through track thickness | full 12 height (through hole) | community | D `plug_cutout` cylinder spans track height |
| Joint play | pegs smaller than sockets; joint stretches 2-3 mm and bends a few degrees | community | G |

## Standard lengths (G, community)

| ID | Name | Length |
|---|---|---|
| A, B, C | Medium straight | 144 |
| A1, B1, C1 | Short straight | 108 |
| A2, B2, C2 | Mini straight | 54 |
| A3 | Middle straight | 72 |
| D | Long straight | 216 |
| U, V | Ramp | 54 |
| H1 | Cross straight | 116 |
| F, G, I, J, L, M (and F1, G1, F2, G2 as listed) | Switches | 144 |

(Brio ID letters used until mid-2000s; the G chart is from the 2002 catalogue.)

## Curve radii (G, community)

| ID | Name | Radius |
|---|---|---|
| E | Large curve | 182 inner ("just over"), ~222 outer |
| E1 | Short curve | 90 |
| T, X | Switch curves | ~88 (approximate, within 2 of E1) |
| O, P, O1, P1 | Short curved switches | 90 |
| Catalogue "diameter" figures | G states they do not correspond to any actual measurement; the small-curve figure is the inside curve diameter | |
| R, S buffer stops | table value 40 but column ambiguous | unverified |

## Printing notes (community)

| Note | Source |
|---|---|
| Female cutout radius = male plug radius + 0.3; library recommends +0.3 to +0.8 | D |
| Plug and track edges bevelled 1 mm to ease joining | D `bevel_width` = 1 |
| A gauge print "if this fits then so will the whole range" listed at 39.5 x 41.5 x 12.2 (Cults3D listing; seen via search only) | https://cults3d.com/en/3d-model/game/wooden-train-track-short-connector |

## Not found / not read

- OpenTrack (opentrack.xyz / zff.dev/chilts/opentrack): site is behind a Cloudflare challenge; not read, no figures used from it.
- Official Brio drawings, peg length and socket depth as stated figures: not found.
- Real joint play tolerance in degrees/mm beyond G's "2-3 mm, few degrees": not found.
