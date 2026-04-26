"""Portfolio class — Stage 3.

OOP showcase. Will hold a list[PortfolioEntry] and implement at least:
- __repr__   → "Portfolio(<n> holdings, total=$X)"
- __len__    → number of holdings
- __iter__   → iterate over PortfolioEntry instances
- __add__    → merge two portfolios (sum quantities for shared symbols)

classmethod:
- from_json(cls, path) — load a Portfolio from disk
"""
