"""BinanceProvider — Stage 2.

Implements BaseProvider against Binance's public market-data API
(https://api.binance.com/api/v3/ticker/24hr). No API key required.
Generous rate limits (~3000 req/min for single-symbol queries) make this
provider well-suited for benchmarking asyncio.gather concurrency.

Key design notes:
- Uses `async with httpx.AsyncClient()` — the canonical asyncio HTTP pattern.
- Maps HTTP 429 → RateLimitError, network/5xx → ProviderUnavailable.
- The `refresh` CLI command will spin up one Provider instance and dispatch
  N concurrent fetch_quote() calls via asyncio.gather().
- Binance returns a flat response (no per-coin wrapping), so this provider
  builds Quote directly via the constructor instead of using
  Quote.from_api_response (which is shaped for CoinGecko's nested response).
"""

from typing import ClassVar

import httpx

from tickr.exceptions import ProviderUnavailable, RateLimitError
from tickr.models import Quote
from tickr.providers.base import BaseProvider


class BinanceProvider(BaseProvider):
    name: ClassVar[str] = "binance"
    BASE_URL: ClassVar[str] = "https://api.binance.com/api/v3"
    # Binance quotes USDT pairs by default; map common symbols to their USDT pair.
    SYMBOL_MAP: ClassVar[dict[str, str]] = {
        "btc": "BTCUSDT",
        "eth": "ETHUSDT",
        "sol": "SOLUSDT",
        "doge": "DOGEUSDT",
        "ada": "ADAUSDT",
    }

    async def fetch_quote(self, symbol: str, currency: str = "usd") -> Quote:
        """Fetch a single quote from Binance's /ticker/24hr endpoint."""
        symbol = symbol.lower()
        if symbol not in self.SYMBOL_MAP:
            raise ProviderUnavailable(f"unknown symbol: {symbol}")
        pair = self.SYMBOL_MAP[symbol]

        url = f"{self.BASE_URL}/ticker/24hr"
        params = {"symbol": pair}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
        except httpx.RequestError as e:
            raise ProviderUnavailable(f"network error: {e}") from e

        if response.status_code == 429:
            raise RateLimitError("binance rate limited (HTTP 429)")
        if not response.is_success:
            raise ProviderUnavailable(
                f"HTTP {response.status_code} from binance: {response.text}"
            )

        try:
            data = response.json()
            price = float(data["lastPrice"])
            change_pct = float(data["priceChangePercent"])
        except (KeyError, ValueError) as e:
            raise ProviderUnavailable(
                f"unexpected response shape from binance: {response.text}"
            ) from e

        return Quote(
            symbol=symbol,
            price=price,
            currency=currency,
            change_pct=change_pct,
        )
