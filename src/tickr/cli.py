"""Typer CLI for tickr.

Stage 0 deliverable: skeleton with three command stubs so `python -m tickr --help`
works end-to-end.  The real implementations land in Stage 4 once models, providers,
portfolio and storage are in place.
"""

from __future__ import annotations

import asyncio   # refresh 命令用

import typer

from tickr.exceptions import TickrError
from tickr.models import PortfolioEntry
from tickr.portfolio import Portfolio
from tickr.providers.binance import BinanceProvider
from tickr.storage import load_portfolio, save_portfolio

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
        None, help="Optional average cost per unit."
    ),
) -> None:
    """Add a holding to the watchlist."""
    # 1. 构造单个 entry → 包成单 entry Portfolio
    new_entry = PortfolioEntry(symbol=symbol, quantity=quantity, avg_cost=avg_cost)
    new_portfolio = Portfolio([new_entry])
    
    # 2. 读现有的 portfolio (storage 处理首次运行的空文件)
    existing = load_portfolio()
    
    # 3. 用 __add__ 合并 —— Stage 3 的设计在这里发光
    merged = existing + new_portfolio
    
    # 4. 写回磁盘
    save_portfolio(merged)
    
    # 5. 反馈 (注意 symbol 在 PortfolioEntry validator 里被 lower 了)
    typer.echo(f"Added: {new_entry.symbol} qty={new_entry.quantity}, avg_cost={new_entry.avg_cost}")
    typer.echo(f"Portfolio now: {merged}")


@app.command(name="list")
def list_cmd() -> None:
    """List all holdings in the current portfolio."""
    portfolio = load_portfolio()
    
    if len(portfolio) == 0:
        typer.echo("Portfolio is empty. Add holdings with: tickr add <symbol> <qty>")
        return
    
    typer.echo(f"{portfolio}\n")
    for entry in portfolio:
        cost_str = f"@ ${entry.avg_cost:,.2f}" if entry.avg_cost else "(no cost recorded)"
        typer.echo(f"  {entry.symbol.upper():6s} qty={entry.quantity:>10.4f}   {cost_str}")


@app.command()
def refresh() -> None:
    """Concurrently refresh quotes for every holding (async)."""
    asyncio.run(_refresh_async())


async def _refresh_async() -> None:
    """The actual async work — kept separate so refresh() can stay sync for typer."""
    portfolio = load_portfolio()

    if len(portfolio) == 0:
        typer.echo("Portfolio is empty. Add holdings with: tickr add <symbol> <qty>")
        return

    provider = BinanceProvider()
    typer.echo(f"Refreshing {len(portfolio)} symbols via {provider.name}...\n")

    try:
        # ⭐ 项目核心:用 gather 把 N 个 fetch_quote 协程并发执行
        quotes = await asyncio.gather(
            *(provider.fetch_quote(e.symbol) for e in portfolio)
        )
    except TickrError as e:
        typer.echo(f"Error fetching quotes: {e}", err=True)
        raise typer.Exit(code=1)

    # 用 Quote.__lt__ 按涨跌幅升序 —— Stage 1 的 dunder 在这里又出场
    for quote in sorted(quotes):
        change_str = (
            f"{quote.change_pct:+6.2f}%" if quote.change_pct is not None else "    n/a"
        )
        typer.echo(
            f"  {quote.symbol.upper():6s} ${quote.price:>12,.2f}   {change_str}"
        )


if __name__ == "__main__":
    app()
