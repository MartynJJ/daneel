"""Daneel command-line interface.

Currently wires up part generation. Slicing (`slice`) and printing (`print`) are
stubbed pending Phase 3/4 — see the roadmap in README.md.
"""

from __future__ import annotations

import typer

from daneel.export import export
from daneel.parts.card import CardParams, build as build_card

app = typer.Typer(help="Parametric CAD-to-print automation for the Bambu P1S.", no_args_is_help=True)


@app.command()
def card(
    text: str = typer.Option("DANEEL", help="Label text."),
    qty: int = typer.Option(1, help="Number of variants (appends an index to the filename)."),
    out: str = typer.Option("output/card.stl", help="Output path (.stl/.step/.3mf)."),
    emboss: bool = typer.Option(True, help="Raised text (--no-emboss for recessed)."),
) -> None:
    """Generate a parametric labelled card and export it."""
    for i in range(qty):
        params = CardParams(text=text, emboss=emboss)
        path = out if qty == 1 else out.replace(".", f"_{i:02d}.", 1)
        written = export(build_card(params), path)
        typer.echo(f"wrote {written}")


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
