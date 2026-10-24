# LEGO Technic - dimensional specs

All mm. Researched 2026-10-24. Tags: **primary**, **derived** (LDraw: 1 LDU = 0.4 mm, read from the official parts library https://library.ldraw.org/library/updates/complete.zip), **community**, **unverified**, **not found**.

No expired Technic patent checked (US 6,461,215 and others via patents.google.com) gives numeric pin/axle/hole dimensions. LDraw values are approximations (see https://www.ldraw.org/article/218.html); Cailliau reports real LDraw deviations of ~0.1-0.2 (https://www.cailliau.org/Alphabetical/L/Lego/Dimensions/More%20Dimensions/BBEditPreviewTemp.html).

## Holes

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Pin hole diameter | 4.8 (radius 6 LDU, p/peghole.dat) | derived | LDraw complete.zip |
| Pin hole, measured / quoted | 4.90 bearing hole (Cailliau); "Ø4.9" quoted as LEGO's figure by forum poster C. Bohnke; 4.95 (partdesigner radius 2.475) | community | cailliau.org URL ; https://forums.ldraw.org/thread-28663-post-56488.html ; https://github.com/marian42/partdesigner (src/measurements.ts) |
| Counterbore diameter | 6.4 (radius 8 LDU, peghole.dat / beamhole.dat) | derived | LDraw complete.zip |
| Counterbore diameter, other | 6.2 (cfinke horizontal_hole_bevel_diameter); 6.0-6.2 range (vibe-cading, attributes to Cailliau but Cailliau's page as read lists no counterbore) | community / unverified | https://github.com/cfinke/LEGO.scad ; https://github.com/fa-mc/vibe-cading/blob/main/docs/lego-technic.md |
| Counterbore depth | 0.8 (2 LDU) | derived | LDraw peghole.dat |
| Counterbore depth, other | 0.9 (cfinke); 0.8-1.0 (vibe-cading) | community / unverified | same two repos |
| Internal length of bearing hole | 6.2 | community (Cailliau) | cailliau.org URL |
| Hole centre height in a brick | 5.8 from base (LDraw 5.6) | community (Cailliau) | cailliau.org URL ; cfinke horizontal_hole_z_offset = 5.8 |
| Hole pitch | 8.0 | derived | LDraw beamhole.dat (20 LDU) |
| Axle hole (cross) tip-to-tip | 4.8 nominal | derived / community | LDraw p/axlehol8.dat (12 LDU); vibe-cading |
| Axle hole arm width | 1.83 nominal (vibe-cading); 2.0 (cfinke axle_spline_width, print-oriented); 1.6 (LDraw axle profile, 4 LDU) | community / derived | vibe-cading ; cfinke ; LDraw p/axle.dat |

## Pins

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Shaft diameter | 4.8 (radius 6 LDU) | derived | LDraw p/connect.dat |
| Shaft diameter, other | 4.63 (partdesigner pinRadius 2.315) | community | partdesigner measurements.ts |
| Half-pin length (one side) | 8.0 (20 LDU) | derived | LDraw p/connect.dat |
| Full pin length | 16.0 (two connect.dat halves, 3673.dat); vibe-cading also 16.0 | derived / community | LDraw parts/3673.dat |
| Collar diameter | 6.4 (radius 8 LDU) | derived | LDraw connect.dat |
| Collar thickness | 0.8 per half (2 LDU), 1.6 total; vibe-cading says 1.8 total | derived / community | LDraw ; vibe-cading |
| End rib (my reading of connect.dat: radius 6.5 LDU, 2 LDU long at each tip) | dia 5.2, 0.8 long | derived, interpretation unverified | LDraw p/connect.dat |
| Core under rib/slot | dia 3.2 (radius 4 LDU) | derived | LDraw connect.dat |
| Friction ribs: 3 ribs, 0.3 high, ~0.6 wide | | unverified | vibe-cading (no stated source) |

## Axles

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Cross tip-to-tip | 4.8 (12 LDU) ; 4.78 (vibe-cading); "axle diameter 4.8" (Cailliau) | derived / community | LDraw p/axle.dat ; vibe-cading ; cailliau.org URL |
| Axle in bearing | ~4.75 shaft vs ~4.9 stud, so axles turn in round holes | unverified (forum snippet; page itself 403) | https://www.eurobricks.com/forum/forums/topic/75308-lego-pin-and-axle-standard |
| Arm width | 1.6 (4 LDU, 2 LDU half-width at x=+-2) | derived | LDraw p/axle.dat |
| Arm width, other | 1.79 (vibe-cading); 1.72 or 2.02 (partdesigner axleSizeInner 0.86 / axleHoleSize 1.01, meaning of half vs full not verified) | community / unverified | vibe-cading ; partdesigner |
| Length unit | 8.0 per stud (Axle 4 = 80 LDU = 32 mm, 3705.dat) | derived | LDraw parts/3705.dat, 4519.dat |
| Bushing/gear-hub height | 7.8 old, 8.0 new; play on axle 0.2 (new) | community (Cailliau) | cailliau.org URL |

## Beams (liftarms)

| Figure | Value | Confidence | Source |
|---|---|---|---|
| Hole pitch | 8.0 | derived | LDraw parts/32523.dat |
| Beam width (thick liftarm, across holes) | 7.2 (18 LDU) | derived | LDraw 32523.dat |
| Beam width, measured | 7.8 ("other beams"), 7.4 for one special brick | community (Cailliau) | cailliau.org URL |
| Beam thickness (hole axis length) | 8.0 (20 LDU) | derived | LDraw 32523.dat |
| Beam thickness, measured | 7.4-7.8 per vibe-cading citing Cailliau | unverified | vibe-cading |
| End radius | 3.9 (vibe-cading, = 7.8/2) ; LDraw 3.6 (9 LDU) | community / derived | vibe-cading ; LDraw |
| Thin liftarm thickness | not found | - | - |
| Gap between brick top and plate | 0.1 | community (Cailliau) | cailliau.org URL |

## Printing notes (sourced, community)

| Note | Source |
|---|---|
| Printed pin hole = nominal 4.8 + 0.10 radial-total -> ~4.90 (slip); friction ~4.7; free rotation 4.9-5.0; loose ~5.1 | https://github.com/fa-mc/vibe-cading/blob/main/docs/lego-technic.md |
| Cross hole arm slot widened a further 0.10 per side on FDM; 0.3 fillet in concave corners printed clean, 0.35 did not (Bambu P1S, PLA) | same |
| LDraw forum: LEGO quoted as 4.9 vs LDraw 4.8, so 4.8 holes print tight | https://forums.ldraw.org/thread-28663-post-56488.html |
| Counterbore chosen at loose end (6.2 x 1.0) so collar seats despite layer lines | vibe-cading |
| Printables "Technic pin hole refining measurements" (Spikes & Spades): listing 403, contents not read | https://www.printables.com/model/660833-lego-technic-pin-hole-refining-measurements-for-3d |

## Not found

- Official LEGO Technic drawings: not found.
- Beam rounded-end radius and thin liftarm cross-section from a primary source: not found.
- Pin retention-groove / friction-rib dimensions from a primary or measured source: not found.
