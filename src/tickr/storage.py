"""Storage — Stage 3.

Currently delegates to Portfolio.from_json / Portfolio.save_json. Kept as a
separate module so future CSV export and other formats can land here without
bloating portfolio.py.
"""
from pathlib import Path

from tickr.portfolio import Portfolio


DEFAULT_PATH = Path("portfolio.json")


def load_portfolio(path: Path = DEFAULT_PATH) -> Portfolio:
    """Load portfolio from disk; return empty if file doesn't exist."""
    if not path.exists():
        return Portfolio()
    return Portfolio.from_json(path)


def save_portfolio(portfolio: Portfolio, path: Path = DEFAULT_PATH) -> None:
    portfolio.save_json(path)