"""Stage 5: tests for models.py.

Will cover:
- Quote validation: bad price (negative), missing fields → ValidationError.
- Quote.from_api_response with a representative CoinGecko payload.
- PortfolioEntry validation.
"""
