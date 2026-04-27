"""BaseProvider — Stage 2.

Abstract base class for any price data source.

    class BaseProvider(ABC):
        name: ClassVar[str]

        @abstractmethod
        async def fetch_quote(self, symbol: str) -> Quote: ...

Subclasses (CoinGeckoProvider, later YahooProvider) implement fetch_quote with
httpx.AsyncClient and translate the raw payload into Quote via classmethod.
"""
from abc import ABC, abstractmethod
from tickr.models import Quote
from typing import ClassVar

class BaseProvider(ABC):
    """Contract every price-data source must implement."""
    name: ClassVar[str]

    @abstractmethod
    async def fetch_quote(self, symbol: str) -> Quote:
        """Fetch a single quote for the given symbol.

        Implementations should raise:
        - RateLimitError on HTTP 429
        - ProviderUnavailable on network failure / 5xx / parse error
        """
        ...