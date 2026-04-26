"""Pydantic models — Stage 1.

Will define:
- Quote        : symbol, price, currency, change_pct, fetched_at
                 + classmethod `from_api_response(cls, data)` to adapt CoinGecko's
                 messy JSON shape into a clean object.
                 + dunder `__lt__` so quotes sort by % change.
- PortfolioEntry : symbol, quantity, avg_cost
"""

from datetime import datetime, UTC
from typing import Annotated
from functools import partial
from pydantic import BaseModel, Field, field_validator

class Quote(BaseModel):
    symbol: str
    price: Annotated[float, Field(gt=0)]
    currency: str = "usd"
    change_pct: float | None = None
    fetched_at: datetime = Field(default_factory=partial(datetime.now, tz=UTC))

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.lower()
    
    @classmethod
    def from_api_response(cls, symbol: str, data: dict, currency: str = "usd") -> "Quote":
        """Adapt CoinGecko /simple/price response into a Quote.

        `data` is the inner dict, e.g. {"usd": 67234.5, "usd_24h_change": 2.34}
        (caller has already unwrapped the outer coin-name key).
        """
        return cls(
            symbol=symbol,
            price=data[currency],
            currency=currency,
            change_pct=data.get(f"{currency}_24h_change"),
        )
    
    def __lt__(self, other: "Quote") -> bool:
        """Sort quotes by 24h change ascending; None counts as the lowest."""
        self_pct = self.change_pct if self.change_pct is not None else float('-inf')
        other_pct = other.change_pct if other.change_pct is not None else float('-inf')
        return self_pct < other_pct
    

class PortfolioEntry(BaseModel):
    symbol: str
    quantity: Annotated[float, Field(gt=0)]
    avg_cost: Annotated[float | None, Field(gt=0)] = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.lower()