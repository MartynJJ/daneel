"""Daneel command-line interface.

    daneel list                       # show registered parts
    daneel make box -s length=120     # build one model, overriding parameters
    daneel batch examples/batch.example.csv   # build many from a spec

Slicing (`slice`) and printing (`print`) are stubbed pending Phase 3/4 —
see the roadmap in README.md.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import typer

from daneel import batch as batchmod
from daneel import registry
from daneel.export import export
from daneel.printlog import PrintLog

app = typer.Typer(help="Parametric CAD-to-print automation for the Bambu P1S.", no_args_is_help=True)

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
    written = export(build(params_cls(**kwargs)), out or f"output/{part}.stl")
    typer.echo(f"wrote {written}")


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
            label=label, part=part, file=file, filament=filament, color=color,
            grams=grams, duration_min=minutes, status=status, rating=rating, notes=notes,
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
            f"{r.id}  {date}  {r.status:11}  {grams:>6}  {mins:>5}  "
            f"{r.label or r.part or ''}"
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
    out: Path = typer.Option(None, "--out", "-o", help="Output .3mf/.gcode (default: alongside input)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the slicer command without running it."),
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


@app.command(name="print")
def print_() -> None:
    """[Phase 4] Send a sliced job to the P1S over LAN."""
    typer.echo("not implemented yet — see roadmap (Phase 4).")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
