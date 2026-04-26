"""Typer CLI for tickr.

Stage 0 deliverable: skeleton with three command stubs so `python -m tickr --help`
works end-to-end.  The real implementations land in Stage 4 once models, providers,
portfolio and storage are in place.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="tickr",
    help="Async multi-source price tracker CLI.",
    no_args_is_help=True,
)


@app.command()
def add(
    symbol: str = typer.Argument(..., help="Symbol to add (e.g. 'btc', 'eth')."),
    quantity: float = typer.Argument(..., help="Quantity held."),
    avg_cost: float | None = typer.Argument(
        None, help="Optional average cost per unit, in the asset's quote currency."
    ),
) -> None:
    """Add a holding to the watchlist."""
    typer.echo(f"[stub] add {symbol} qty={quantity} avg_cost={avg_cost}")
    typer.echo("       → real implementation lands in Stage 4 (cli.py wiring).")


@app.command(name="list")
def list_cmd() -> None:
    """List all holdings in the current portfolio."""
    typer.echo("[stub] list — will read portfolio.json and print a table.")


@app.command()
def refresh() -> None:
    """Concurrently refresh quotes for every holding (async)."""
    typer.echo(
        "[stub] refresh — will use asyncio.gather() over Provider.fetch_quote(...)."
    )


if __name__ == "__main__":
    app()
