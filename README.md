# Daneel

> *"A robot may not injure a human being... but it may absolutely print them a nice parametric tray."*

Named after R. Daneel Olivaw — Asimov's tireless, meticulous humaniform robot — **Daneel** is a
Python toolkit that automates the full pipeline from parametric CAD to a finished print on a
**Bambu Lab P1S**:

```
parameters ──▶ CadQuery model ──▶ STL/STEP ──▶ slice (3MF/G-code) ──▶ send to P1S ──▶ print
```

The goal: define a part once as code, then batch-generate variants ("cards", tags, labels,
inserts, organizers) and get them onto the printer with a single command — no manual clicking
through the modeller or slicer.

## Why

Designing repetitive parts by hand is slow and error-prone. Daneel treats parts as **parametric
functions**: give it dimensions/text/quantity and it produces geometry, slices it with sane P1S
profiles, and dispatches the job over the network.

## Status

🚧 Early scaffolding. See the roadmap below. Nothing here is stable yet.

## Features (roadmap)

### Phase 1 — Parametric part library ✅ (scaffolded)
- [x] CadQuery-based part definitions (`src/daneel/parts/`)
- [x] Example: parametric **card / label tag** with embossed text
- [ ] Gridfinity-compatible bins & baseplates
- [ ] Cable clips, drawer inserts, hooks (common household parts)
- [ ] Parameter validation + sensible defaults per part

### Phase 2 — Export & batch generation
- [ ] Export to STL / STEP / 3MF from a single call
- [ ] Batch driver: generate N variants from a CSV / YAML spec
- [ ] Deterministic output naming + a manifest of what was produced

### Phase 3 — Slicing automation
- [ ] Headless slicing via **Bambu Studio / OrcaSlicer** CLI
- [ ] P1S machine + filament profiles checked into the repo
- [ ] Per-part slicing overrides (layer height, infill, supports)
- [ ] Produce ready-to-print `.3mf` / `.gcode`

### Phase 4 — Printer dispatch
- [ ] Send jobs to the P1S over the network (MQTT / LAN mode via [`bambulabs-api`] or `pybambu`)
- [ ] Query printer state (idle / printing / error, temps, progress)
- [ ] AMS filament awareness — pick the right slot
- [ ] Print queue: enqueue a batch, print sequentially

### Phase 5 — Ergonomics
- [ ] `daneel` CLI (`daneel make card --text "A-17" --qty 4 --print`)
- [ ] Config file for printer IP / access code / serial
- [ ] Optional web UI for triggering parametric prints
- [ ] Preview renders (PNG) before committing to a print

## Quick start

```bash
# clone + install (editable)
git clone git@github.com:MartynJJ/daneel.git
cd daneel
python -m venv .venv && source .venv/bin/activate
pip install -e .

# generate an example card as STL
python -m daneel.parts.card --text "A-17" --out output/card.stl
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
│   │   └── card.py     # example: labelled card/tag
│   ├── config.py       # printer/slicer configuration
│   └── cli.py          # command-line entry point (stub)
├── examples/           # example specs (CSV/YAML batches)
├── output/             # generated artifacts (git-ignored)
└── pyproject.toml
```

## License

MIT — see [LICENSE](LICENSE).

[`bambulabs-api`]: https://github.com/mattcar15/bambu-lab-api
