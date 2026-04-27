"""Tests for tickr.providers.binance.BinanceProvider.

We use `respx` to mock httpx at the transport level — tests don't actually hit
Binance, so they're fast, deterministic, and work offline.
"""

import asyncio

import httpx
import pytest
import respx

from tickr.exceptions import ProviderUnavailable, RateLimitError
from tickr.models import Quote
from tickr.providers.binance import BinanceProvider


BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"


# -------- helpers --------

def binance_payload(pair: str, price: str = "50000.0", change: str = "1.5") -> dict:
    """Build a minimal Binance /ticker/24hr response payload."""
    return {"symbol": pair, "lastPrice": price, "priceChangePercent": change}


# -------- happy path --------

class TestSuccessfulFetch:
    @respx.mock
    async def test_fetch_quote_returns_quote(self):
        respx.get(BINANCE_URL, params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(200, json=binance_payload("BTCUSDT", "78500.50", "2.34"))
        )

        provider = BinanceProvider()
        quote = await provider.fetch_quote("btc")

        assert isinstance(quote, Quote)
        assert quote.symbol == "btc"
        assert quote.price == 78500.50
        assert quote.change_pct == 2.34
        assert quote.currency == "usd"

    @respx.mock
    async def test_uppercase_symbol_normalized(self):
        respx.get(BINANCE_URL, params={"symbol": "ETHUSDT"}).mock(
            return_value=httpx.Response(200, json=binance_payload("ETHUSDT", "3000.0", "0.5"))
        )

        provider = BinanceProvider()
        # Pass uppercase — BinanceProvider should lower it before SYMBOL_MAP lookup
        quote = await provider.fetch_quote("ETH")
        assert quote.symbol == "eth"


# -------- error paths --------

class TestErrorHandling:
    async def test_unknown_symbol_raises_provider_unavailable(self):
        # No HTTP mock needed — should fail before any request
        provider = BinanceProvider()
        with pytest.raises(ProviderUnavailable):
            await provider.fetch_quote("not-a-real-coin")

    @respx.mock
    async def test_429_raises_rate_limit_error(self):
        respx.get(BINANCE_URL, params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(429, json={"code": -1003, "msg": "Too many requests"})
        )

        provider = BinanceProvider()
        with pytest.raises(RateLimitError):
            await provider.fetch_quote("btc")

    @respx.mock
    async def test_500_raises_provider_unavailable(self):
        respx.get(BINANCE_URL, params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        provider = BinanceProvider()
        with pytest.raises(ProviderUnavailable):
            await provider.fetch_quote("btc")

    @respx.mock
    async def test_malformed_json_raises_provider_unavailable(self):
        respx.get(BINANCE_URL, params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(200, text="<html>not json</html>")
        )

        provider = BinanceProvider()
        with pytest.raises(ProviderUnavailable):
            await provider.fetch_quote("btc")

    @respx.mock
    async def test_missing_required_field_raises_provider_unavailable(self):
        # API returns 200 + valid JSON but missing 'lastPrice' field
        respx.get(BINANCE_URL, params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(200, json={"symbol": "BTCUSDT"})
        )

        provider = BinanceProvider()
        with pytest.raises(ProviderUnavailable):
            await provider.fetch_quote("btc")


# -------- concurrency --------

class TestConcurrency:
    @respx.mock
    async def test_gather_fetches_concurrently(self):
        # Mock all three pairs
        for pair, price in [("BTCUSDT", "78000"), ("ETHUSDT", "3000"), ("SOLUSDT", "200")]:
            respx.get(BINANCE_URL, params={"symbol": pair}).mock(
                return_value=httpx.Response(200, json=binance_payload(pair, price, "1.0"))
            )

        provider = BinanceProvider()
        symbols = ["btc", "eth", "sol"]
        quotes = await asyncio.gather(*(provider.fetch_quote(s) for s in symbols))

        assert len(quotes) == 3
        assert {q.symbol for q in quotes} == {"btc", "eth", "sol"}
