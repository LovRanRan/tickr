"""CoinGeckoProvider — Stage 2.

Implements BaseProvider against the public CoinGecko API
(https://api.coingecko.com/api/v3/simple/price). Free, no API key required.

Key design notes:
- Uses `async with httpx.AsyncClient()` — the canonical asyncio HTTP pattern.
- Maps HTTP 429 → RateLimitError, network/5xx → ProviderUnavailable.
- The `refresh` CLI command will spin up one Provider instance and dispatch
  N concurrent fetch_quote() calls via asyncio.gather().
"""
