"""Pydantic models — Stage 1.

Will define:
- Quote        : symbol, price, currency, change_pct, fetched_at
                 + classmethod `from_api_response(cls, data)` to adapt CoinGecko's
                 messy JSON shape into a clean object.
                 + dunder `__lt__` so quotes sort by % change.
- PortfolioEntry : symbol, quantity, avg_cost
"""
