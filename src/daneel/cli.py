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

app = typer.Typer(help="Parametric CAD-to-print automation for the Bambu P1S.", no_args_is_help=True)


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


@app.command()
def slice() -> None:  # noqa: A001 - matches user-facing verb
    """[Phase 3] Slice an exported model with Bambu Studio / OrcaSlicer CLI."""
    typer.echo("not implemented yet — see roadmap (Phase 3).")
    raise typer.Exit(code=1)


@app.command(name="print")
def print_() -> None:
    """[Phase 4] Send a sliced job to the P1S over LAN."""
    typer.echo("not implemented yet — see roadmap (Phase 4).")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
