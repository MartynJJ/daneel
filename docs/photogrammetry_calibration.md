# Photogrammetry calibration cube + scan-to-print (Phase 6 spec)

Reverse of daneel's CAD→print flow: **real object → photos → photogrammetry →
mesh/STL → daneel `slice → preview → print`**. daneel does **not** do the 3D
reconstruction (that's Meshroom / AliceVision, COLMAP, RealityCapture, Metashape,
or a phone app like Polycam / KIRI). daneel owns two touchpoints:

1. **Print the calibration reference** used during capture — the `calib_cube` part below.
2. **Consume the scan** — `daneel import <mesh>` to make a photogrammetry STL printable.

---

## Part: `calib_cube`

**Why it exists.** Structure-from-motion recovers *shape* but not *absolute scale*
(monocular scale ambiguity), and struggles on featureless/reflective subjects.
Placing a known-geometry, marker-bearing object beside the subject fixes both:
its measured size sets **metric scale**, and its markers give the solver robust,
uniquely-identifiable **fiducials** (many tools auto-detect ArUco/coded targets and
register them).

### Geometry
- Parametric cube, default edge `size = 40.0` mm.
  - The **printed** dimension is the ground truth — measure the real print with
    calipers and feed *that* to the solver, not nominal (FDM is ±0.1–0.2 mm ≈ 0.3–0.5 %).
- Each of the 6 faces has a recessed square **pocket** to seat a laser-printed
  marker card flush and coplanar:
  - `recess_depth = 0.6` mm, `pocket_margin = 3` mm (white quiet-zone border ArUco needs).
  - Recess + paper markers rather than printing markers directly: a single-nozzle
    FDM machine can't make crisp black/white tonal contrast, and ArUco detection needs
    tone, not relief. Paper markers detect far more reliably.
- **Origin keying:** chamfer one corner (`origin_chamfer = 3` mm) so the cube's
  coordinate frame is unambiguous in the reconstruction / for re-orienting the scan.
- Optional embossed face index beside each pocket.

### Markers
- ArUco dictionary `4x4_50` (configurable via `dict`), 6 distinct IDs
  (`marker_ids`, default `0..5`), one per face.
- daneel emits a companion **marker sheet** (`calib_cube_markers.pdf`, A4/Letter):
  the 6 markers at **exact physical size** = `size - 2*pocket_margin`, plus crop marks
  and a printed scale bar for a caliper sanity-check. Print at **100 % / no scaling**,
  cut, glue into the pockets.
- Known marker edge + known cube geometry ⇒ solver sets metric scale.

### Params (registry entry)
`size`, `dict`, `marker_ids[6]`, `pocket_margin`, `recess_depth`, `origin_chamfer`,
`sheet_format` (a4|letter), `with_pockets` (bool — flat faces if you'll tape markers on).

### Outputs
- `calib_cube.stl` — print in **matte white / light** PLA (gloss and dark colors hurt detection).
- `calib_cube_markers.pdf` — the marker sheet.
- Metadata sidecar: nominal cube size + marker size → later used as the scale input.

### Dependencies
Optional extra `[scan]`. Two ways to render markers:
- `opencv-contrib-python` (`cv2.aruco.generateImageMarker`) — easiest, reliable, heavy dep.
- **SVG-direct** — ArUco dictionary bit patterns are deterministic; render the grid +
  black border straight to SVG/PDF. Keeps deps light; preferred if we don't otherwise need cv2.

### CLI
`daneel make calib_cube --set size=50` → STL + marker PDF, then `slice → preview → print`.

---

## `daneel import <mesh>` (scan intake, later)

Photogrammetry meshes are typically **non-manifold, high-poly, un-scaled, arbitrarily
oriented**. Intake steps before slicing:
- validate + repair (fill holes, remove non-manifold edges) — trimesh / pymeshlab.
- apply **scale** from the calib cube (measured size ÷ reconstructed size).
- re-orient to a sensible print bed placement (flat face down; use the cube's origin corner).
- optional decimate to a sane triangle count.
→ hand the cleaned STL to the existing `slice → preview → print` pipeline.

**Out of scope:** reconstruction itself. daneel prints the target and consumes the result.

## Capture checklist (docs for the user)
- 30–100+ sharp, evenly-lit photos, high overlap, orbit the subject at 2–3 heights.
- Cube in frame in enough shots (doesn't need to be in *every* shot once registered).
- Avoid shiny/transparent/dark/textureless subjects — they fail regardless of the cube.
- Matte cube, diffuse light, no harsh shadows across the markers.
