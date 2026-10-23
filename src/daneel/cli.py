"""Daneel command-line interface.

    daneel list                       # show registered parts
    daneel make box -s length=120     # build one model, overriding parameters
    daneel batch examples/batch.example.csv   # build many from a spec

Slicing (`slice`), printing (`print`) and `status` need the slicer / printer
configured - see README.md.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import typer

from daneel import batch as batchmod
from daneel import registry
from daneel.export import export
from daneel.printlog import PrintLog

app = typer.Typer(
    help="Parametric CAD-to-print automation for the Bambu P1S.", no_args_is_help=True
)

log_app = typer.Typer(help="Track completed prints.", no_args_is_help=True)
app.add_typer(log_app, name="log")


@app.command(name="list")
def list_parts() -> None:
    """List registered parts and their parameters."""
    for name in registry.available():
        params_cls, _ = registry.get(name)
        names = ", ".join(f.name for f in fields(params_cls))
        typer.echo(f"{name}: {names}")


@app.command()
def make(
    part: str = typer.Argument(..., help="Part name (see `daneel list`)."),
    out: str = typer.Option(None, "--out", "-o", help="Output path (.stl/.step/.3mf)."),
    set_values: list[str] = typer.Option(
        [], "--set", "-s", help="Override a parameter, e.g. -s length=120 (repeatable)."
    ),
) -> None:
    """Build a single model, overriding any parameters with --set."""
    params_cls, build = registry.get(part)
    field_types = {f.name: f.type for f in fields(params_cls)}
    kwargs = {}
    for item in set_values:
        key, _, value = item.partition("=")
        if key not in field_types:
            raise typer.BadParameter(f"part {part!r} has no parameter {key!r}")
        kwargs[key] = batchmod.coerce(field_types[key], value)
    params = params_cls(**kwargs)
    written = export(build(params), out or f"output/{part}.stl")
    typer.echo(f"wrote {written}")
    make_companions = registry.companions(part)
    if make_companions:
        for extra in make_companions(params, written) or []:
            typer.echo(f"wrote {extra}")


@app.command()
def batch(
    spec: Path = typer.Argument(..., help="CSV/YAML spec file."),
    outdir: Path = typer.Option(Path("output"), "--outdir", help="Output directory."),
    fmt: str = typer.Option("stl", "--fmt", help="Default export format."),
    part: str = typer.Option(None, "--part", help="Default part when the spec omits one."),
) -> None:
    """Build many models from a spec file, writing a manifest.json."""
    manifest = batchmod.run(spec, outdir, fmt, default_part=part)
    typer.echo(f"generated {len(manifest)} model(s) -> {outdir}/manifest.json")


@log_app.command("add")
def log_add(
    label: str = typer.Argument(None, help="Human description of the print."),
    part: str = typer.Option(None, "--part", help="Registry part name, if applicable."),
    file: str = typer.Option(None, "--file", help="Source model / sliced file."),
    filament: str = typer.Option(None, "--filament", help='e.g. "PLA Basic".'),
    color: str = typer.Option(None, "--color"),
    grams: float = typer.Option(None, "--grams", help="Filament used."),
    minutes: float = typer.Option(None, "--minutes", help="Print duration."),
    status: str = typer.Option("success", "--status", help="success|failed|aborted|in_progress."),
    rating: int = typer.Option(None, "--rating", help="Subjective 1-5."),
    notes: str = typer.Option(None, "--notes"),
) -> None:
    """Record a completed print."""
    try:
        record = PrintLog().add(
            label=label,
            part=part,
            file=file,
            filament=filament,
            color=color,
            grams=grams,
            duration_min=minutes,
            status=status,
            rating=rating,
            notes=notes,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"logged {record.id} [{record.status}] {record.label or record.part or ''}")


@log_app.command("list")
def log_list(
    limit: int = typer.Option(20, "--limit", "-n", help="Show the most recent N."),
    status: str = typer.Option(None, "--status", help="Filter by status."),
) -> None:
    """List logged prints, most recent last."""
    records = PrintLog().records()
    if status:
        records = [r for r in records if r.status == status]
    if not records:
        typer.echo("no prints logged yet.")
        return
    for r in records[-limit:]:
        date = r.timestamp[:10]
        grams = f"{r.grams:.0f}g" if r.grams else "-"
        mins = f"{r.duration_min:.0f}m" if r.duration_min else "-"
        typer.echo(
            f"{r.id}  {date}  {r.status:11}  {grams:>6}  {mins:>5}  {r.label or r.part or ''}"
        )


@log_app.command("stats")
def log_stats() -> None:
    """Show aggregate print statistics."""
    s = PrintLog().summary()
    if s["total"] == 0:
        typer.echo("no prints logged yet.")
        return
    rate = f"{s['success_rate'] * 100:.0f}%" if s["success_rate"] is not None else "n/a"
    typer.echo(f"prints:        {s['total']}")
    typer.echo(f"success rate:  {rate}")
    typer.echo(f"filament used: {s['total_grams']:.0f} g")
    typer.echo(f"print time:    {s['total_hours']:.1f} h")
    typer.echo("by status:     " + ", ".join(f"{k}={v}" for k, v in sorted(s["by_status"].items())))
    typer.echo("by part:       " + ", ".join(f"{k}={v}" for k, v in sorted(s["by_part"].items())))


@app.command()
def slice(  # noqa: A001 - matches user-facing verb
    model: Path = typer.Argument(..., help="Input model (.stl/.step)."),
    out: Path = typer.Option(
        None, "--out", "-o", help="Output .3mf/.gcode (default: alongside input)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the slicer command without running it."
    ),
) -> None:
    """Slice a model with the configured Bambu Studio / OrcaSlicer binary."""
    from daneel.config import load
    from daneel.slice import SlicerError, SlicerInterface

    iface = SlicerInterface(load().slicer)
    try:
        result = iface.slice(model, out, dry_run=dry_run)
    except SlicerError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if dry_run:
        typer.echo(" ".join(result.command))
        return
    typer.echo(f"sliced -> {result.output}")
    if result.duration_min is not None:
        typer.echo(f"  est. time: {result.duration_min:.0f} min")
    if result.grams is not None:
        typer.echo(f"  filament:  {result.grams:.1f} g")


@app.command()
def status() -> None:
    """Show live P1S status."""
    from daneel.config import load
    from daneel.dispatch import P1S, DispatchError

    cfg = load().printer
    if cfg is None:
        raise typer.BadParameter("no [printer] section in config")
    try:
        with P1S(cfg) as p:
            st = p.status()
    except DispatchError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(f"state:  {st.state}")
    typer.echo(f"bed:    {st.bed_temp}C  nozzle: {st.nozzle_temp}C")
    if st.busy:
        typer.echo(f"job:    {st.file}  {st.percent}%  {st.remaining_min} min left")


def _control(action: str) -> None:
    from daneel.config import load
    from daneel.dispatch import P1S, DispatchError

    cfg = load().printer
    if cfg is None:
        raise typer.BadParameter("no [printer] section in config")
    try:
        with P1S(cfg) as p:
            ok = getattr(p, action)()
    except DispatchError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(f"{action}: {'ok' if ok else 'printer did not accept the command'}")
    if not ok:
        raise typer.Exit(code=1)


@app.command()
def pause() -> None:
    """Pause the current print."""
    _control("pause")


@app.command()
def resume() -> None:
    """Resume a paused print."""
    _control("resume")


@app.command()
def stop(yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation.")) -> None:
    """Abort the current print."""
    if not yes and not typer.confirm("Abort the running print?"):
        raise typer.Exit(code=1)
    _control("stop")


profile_app = typer.Typer(help="Slicer preset helpers.", no_args_is_help=True)
app.add_typer(profile_app, name="profile")


@profile_app.command("flatten")
def profile_flatten(
    preset: Path = typer.Argument(..., help="Preset .json (parents are read from its folder)."),
    out: Path = typer.Option(..., "--out", "-o", help="Where to write the flattened preset."),
) -> None:
    """Resolve `inherits` so the headless slicer sees values like filament density."""
    import json

    from daneel.profiles import ProfileError, flatten

    try:
        merged = flatten(preset)
    except ProfileError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=4))
    typer.echo(f"wrote {out} ({len(merged)} settings)")


@app.command(name="print")
def print_(
    job: Path = typer.Argument(..., help="Sliced .3mf (from `daneel slice`)."),
    part: str = typer.Option(None, "--part", help="Registry part name for the log."),
    filament: str = typer.Option(None, "--filament", help='e.g. "PLA Basic".'),
    ams: bool = typer.Option(False, "--ams/--no-ams", help="Use AMS (default: external spool)."),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Monitor and auto-log on finish."),
    upload_only: bool = typer.Option(
        False,
        "--upload-only",
        help="Upload to the printer but do not start (start it from the screen/app).",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Upload a sliced 3MF to the P1S, start it, and log the outcome."""
    from daneel.config import load
    from daneel.dispatch import P1S, DispatchError, PrinterStatus, watch
    from daneel.slice import read_3mf_estimates

    cfg = load().printer
    if cfg is None:
        raise typer.BadParameter("no [printer] section in config")
    if not job.exists() or job.suffix != ".3mf":
        raise typer.BadParameter(f"{job} is not a .3mf file")
    minutes, grams = read_3mf_estimates(job)
    est = f"~{minutes:.0f} min" if minutes else "unknown time"
    est += f", {grams:.1f} g" if grams else ""
    last = [""]

    def show(s: PrinterStatus) -> None:
        line = f"{s.state} {s.percent}% {s.remaining_min}m"
        if line != last[0]:
            typer.echo(line)
            last[0] = line

    try:
        with P1S(cfg) as p:
            st = p.status()
            if st.busy:
                typer.echo(f"printer busy ({st.state}, {st.percent}%) - refusing to start")
                raise typer.Exit(code=1)
            verb = "Upload" if upload_only else "Start"
            if not yes and not typer.confirm(
                f"{verb} {job.name} ({est}) on the P1S?"
                + ("" if upload_only else " Bed must be clear.")
            ):
                raise typer.Exit(code=1)
            name = p.upload(job)
            typer.echo(f"uploaded {name}")
            if upload_only:
                typer.echo("not started - start it from the printer screen or app")
                return
            p.start(name, use_ams=ams)
            typer.echo("started")
            if not wait:
                return
            rec = watch(p, job, part=part, filament=filament, on_status=show)
    except DispatchError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(f"logged {rec.id} [{rec.status}]")


if __name__ == "__main__":
    app()
