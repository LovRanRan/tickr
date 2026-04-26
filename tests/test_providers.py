"""Stage 5: tests for providers/coingecko.py (async).

Will use respx to mock httpx so tests don't hit the real CoinGecko API.

Will cover:
- Successful fetch_quote returns a valid Quote.
- HTTP 429 raises RateLimitError.
- HTTP 5xx / network error raises ProviderUnavailable.
- asyncio.gather over multiple symbols completes concurrently.
"""
