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
- [x] Stock parts: labelled tag (`card`), open-top box, L-bracket with mounting holes
- [x] Part registry (`daneel list`) — register a new part with one line
- [x] Parameter validation + sensible defaults per part
- [ ] More stock parts: spacers, cable clips, drawer inserts, hooks
- [ ] Gridfinity-compatible bins & baseplates

### Phase 2 — Export & batch generation ✅
- [x] Export to STL / STEP / 3MF from a single call (`daneel make`)
- [x] Batch driver: generate N models/variants from a CSV / YAML spec (`daneel batch`)
- [x] Deterministic output naming + a `manifest.json` of what was produced

### Phase 3 — Slicing automation 🚧
- [x] Headless slicing via **Bambu Studio / OrcaSlicer** CLI (`daneel slice`)
- [x] Profile-driven (machine / process / filament) via config
- [x] Parse slicer estimates (print time + filament grams)
- [x] `--dry-run` to inspect the exact command; produces `.3mf` / `.gcode`
- [ ] **Validate flag surface against a real P1S** (flags vary by slicer version)
- [ ] Per-part slicing overrides (layer height, infill, supports)

### Phase 3.5 — Print log ✅
- [x] Append-only JSONL log of every completed print (`daneel log add`)
- [x] List and filter history (`daneel log list`)
- [x] Aggregate stats: count, success rate, filament used, print hours (`daneel log stats`)
- [ ] Auto-append from printer telemetry (arrives with Phase 4)

### Phase 4 — Printer dispatch
- [ ] Send jobs to the P1S over the network (MQTT / LAN mode via [`bambulabs-api`])
- [ ] Query printer state (idle / printing / error, temps, progress)
- [ ] AMS filament awareness — pick the right slot
- [ ] Print queue: enqueue a batch, print sequentially
- [ ] Auto-log each finished print into the print log

### Phase 5 — Ergonomics
- [ ] `daneel` CLI (`daneel make <part> --print`)
- [ ] Config file for printer IP / access code / serial
- [ ] Optional web UI for triggering parametric prints
- [ ] Preview renders (PNG) before committing to a print

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
│   │   └── bracket.py  # L-bracket with mounting holes
│   ├── registry.py     # name -> part lookup (daneel list)
│   ├── batch.py        # CSV/YAML batch driver + manifest
│   ├── printlog.py     # append-only print history (daneel log)
│   ├── slice.py        # headless slicer wrapper (daneel slice)
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
