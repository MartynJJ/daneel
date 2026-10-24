# Daneel

> *"A robot may not injure a human being... but it may absolutely print them a nice parametric bracket."*

Named after R. Daneel Olivaw — Asimov's tireless, meticulous humaniform robot — **Daneel** is a
Python toolkit that automates the full pipeline from **parametric CAD** to a finished print on a
**Bambu Lab P1S**:

```
parameters ──▶ CadQuery model ──▶ STL/STEP ──▶ slice (3MF/G-code) ──▶ send to P1S ──▶ print
```

The goal: define a part once as code, then generate CAD models (and variants of them) and get them
onto the printer with a single command — no manual clicking through the modeller or slicer.

## Why

Designing parts by hand in a GUI is slow and hard to reproduce. Daneel treats CAD as **code**: each
part is a parametric function that takes dimensions/options and returns geometry. From there Daneel
exports it, slices it with sane P1S profiles, and dispatches the job over the network — scriptable,
version-controllable, and batchable.

## Status

🚧 Early scaffolding. See the roadmap below. Nothing here is stable yet.

## Features (roadmap)

### Phase 1 — Parametric part library ✅
- [x] CadQuery-based part definitions (`src/daneel/parts/`) — each is a `build(params)` function
- [x] Stock parts: labelled tag (`card`), open-top box, L-bracket with mounting holes, screw-top `jar`
- [x] Part registry (`daneel list`) — register a new part with one line
- [x] Parameter validation + sensible defaults per part
- [ ] More stock parts: spacers, cable clips, drawer inserts, hooks
- [ ] Gridfinity-compatible bins & baseplates

### Phase 2 — Export & batch generation ✅
- [x] Export to STL / STEP / 3MF from a single call (`daneel make`)
- [x] Batch driver: generate N models/variants from a CSV / YAML spec (`daneel batch`)
- [x] Deterministic output naming + a `manifest.json` of what was produced

### Phase 3 — Slicing automation ✅
- [x] Headless slicing via the **OrcaSlicer** CLI (`daneel slice`)
- [x] Profile-driven (machine / process / filament) via config
- [x] Parse estimates (print time + filament grams) from the exported 3MF
- [x] `--dry-run` to inspect the exact command; produces a printable `.3mf`
- [x] **Validated end-to-end against OrcaSlicer 2.4.1 + real P1S profiles** (see notes below)
- [ ] Per-part slicing overrides (layer height, infill, supports)

**Validation notes (OrcaSlicer 2.4.1):** there is no `--export-gcode` (G-code is
embedded in the 3MF, which is what the P1S prints); `--arrange 1 --slice 0` are
required; estimates live in the 3MF at `Metadata/slice_info.config`, not stdout;
and the P1S process presets are grouped under `@BBL X1C`. The build plate comes from
`slicer.bed_type` (default `Textured PEI Plate`, the P1S stock plate: 65 C PLA bed plus
Bambu's Z trim); the slicer otherwise defaults to Cool Plate (35 C), wrong for textured PEI. Headless machines run
the AppImage via `xvfb-run … AppRun`. Real-slice validation also caught (and
fixed) a bracket geometry bug where vertical-leg holes severed the leg.

### Phase 3.5 — Print log ✅
- [x] Append-only JSONL log of every completed print (`daneel log add`)
- [x] List and filter history (`daneel log list`)
- [x] Aggregate stats: count, success rate, filament used, print hours (`daneel log stats`)
- [x] Auto-append from printer telemetry (`daneel print` logs on finish)

### Phase 4 — Printer dispatch
- [x] Send jobs to the P1S over the network (MQTT / LAN mode via [`bambulabs-api`]) — `daneel print`
- [x] Query printer state (idle / printing / error, temps, progress) — `daneel status`
- [ ] AMS filament awareness — pick the right slot
- [ ] Print queue: enqueue a batch, print sequentially
- [x] Auto-log each finished print into the print log (unit-tested; awaiting first real print)

### Phase 5 — Ergonomics
- [ ] `daneel` CLI (`daneel make <part> --print`)
- [ ] Config file for printer IP / access code / serial
- [ ] Optional web UI for triggering parametric prints
- [ ] Preview renders (PNG) before committing to a print

## Screw-top jar

`jar` builds a cylindrical container and a threaded lid from one parameter set, so they always
fit. Threads are a trapezoid swept along a helix (shallow flanks, no supports). `clearance`
(default 0.3 mm) is the printer-specific fit allowance: print the short thread-only pair first
and tune it before committing to a full jar.

```bash
daneel make jar -s piece=test      # ~2.5-pitch neck + matching lid ring; print this first
daneel make jar                    # body and lid side by side
daneel make jar -s piece=lid -s clearance=0.4
```

OCC booleans with helical faces can silently drop an operand, so thread unions use a fuzzy
tolerance and fail loudly if the volume does not grow. The tests check fit by moving the lid
along the helix (zero overlap) and off it (collision).

## Adding a part

A part is just a module in `src/daneel/parts/` exposing a `build(params)` that returns a CadQuery
`Workplane`. The included `card.py` (a labelled tag) is the reference example — copy it as a
template for boxes, brackets, or whatever you need next.

## Quick start

```bash
# clone + install (editable)
git clone git@github.com:MartynJJ/daneel.git
cd daneel
python -m venv .venv && source .venv/bin/activate
pip install -e .

# list available parts and their parameters
daneel list

# build a single model, overriding parameters
daneel make box --set length=120 --set height=40 --out output/box.stl

# build many models from a spec, with a manifest
daneel batch examples/batch.example.yaml

# slice a model for the P1S (see the command first with --dry-run)
daneel slice output/bracket.stl --dry-run
daneel slice output/bracket.stl -o output/bracket.3mf

# live printer state, then send a sliced job (confirms, uploads, starts, monitors, auto-logs)
# needs a [printer] section in the config: ip, serial, access_code (LAN mode)
daneel status
daneel print output/bracket.3mf --part bracket --filament "PLA Basic"   # --ams for AMS

# NOTE: current Bambu firmware rejects third-party start commands (HMS 0500-0500-0001-0007,
# "MQTT command verification failed") unless the printer has LAN Only Mode and then
# Developer Mode switched on (printer screen: Settings > Network). Cloud/Handy control is
# off while LAN Only Mode is on.

# stage a job without starting it (FTPS only; works with LAN Only Mode off, so the Handy app
# keeps working: start from the printer screen/app). status/pause/resume/stop/auto-log need
# MQTT, which is only open in LAN Only Mode
daneel print output/bracket.3mf --upload-only
daneel pause
daneel resume
daneel stop

# pre-flight page from the real toolpaths (make + slice + view in one step, or any sliced 3MF)
daneel preview box -s length=30
daneel preview output/bracket.3mf

# scan intake: repair, scale (from the calib cube) and bed-seat a photogrammetry mesh
daneel import scan.obj --ref-real 20.0 --ref-model 0.482 --max-faces 200000

# manage job files on the printer's storage (FTPS only)
daneel files list
daneel files rm calib_cube_20.3mf

# the CLI doesn't resolve preset inheritance, so system filament presets slice as 0 g (and with
# root-default cooling values). Flatten one once, then point slicer.filament_profile at it
daneel profile flatten "/opt/orca/resources/profiles/BBL/filament/Generic PLA High Speed @BBL P1P.json" \
    -o ~/.config/daneel/profiles/pla.json

# log a finished print and review progress
daneel log add "desk hook v2" --part bracket --filament "PLA Basic" --grams 14 --minutes 52
daneel log list
daneel log stats
```

> **Note:** CadQuery pulls in the OCP (OpenCascade) geometry kernel, which is a large dependency.
> Installing into an isolated virtualenv is strongly recommended.

## Printer

- **Model:** Bambu Lab P1S (CoreXY, enclosed, AMS-capable)
- **Slicers:** Bambu Studio / OrcaSlicer (headless CLI for automation)
- **Control:** LAN mode preferred — access code + serial + local IP. Never commit credentials;
  put them in `~/.config/daneel/config.toml` or environment variables.

## Layout

```
daneel/
├── src/daneel/
│   ├── parts/          # parametric CadQuery part definitions
│   │   ├── card.py     # labelled tag
│   │   ├── box.py      # open-top box / container
│   │   ├── bracket.py  # L-bracket with mounting holes
│   │   ├── jar.py      # screw-top jar + threaded lid (helical threads)
│   │   └── threads.py  # helical thread sweep helpers
│   ├── registry.py     # name -> part lookup (daneel list)
│   ├── batch.py        # CSV/YAML batch driver + manifest
│   ├── printlog.py     # append-only print history (daneel log)
│   ├── slice.py        # headless slicer wrapper (daneel slice)
│   ├── dispatch.py     # P1S upload/start/monitor + auto-log (daneel print/status/pause/stop)
│   ├── profiles.py     # flatten slicer presets (daneel profile flatten)
│   ├── scan.py         # photogrammetry mesh intake (daneel import)
│   ├── preview.py      # toolpath pre-flight page from a sliced 3MF (daneel preview)
│   ├── export.py       # STL/STEP/3MF export
│   ├── config.py       # printer/slicer configuration
│   └── cli.py          # command-line entry point
├── examples/           # example batch specs (CSV/YAML)
├── output/             # generated artifacts (git-ignored)
└── pyproject.toml
```

## License

MIT — see [LICENSE](LICENSE).

[`bambulabs-api`]: https://github.com/mattcar15/bambu-lab-api
