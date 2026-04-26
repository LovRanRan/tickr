"""BaseProvider — Stage 2.

Abstract base class for any price data source.

    class BaseProvider(ABC):
        name: ClassVar[str]

        @abstractmethod
        async def fetch_quote(self, symbol: str) -> Quote: ...

Subclasses (CoinGeckoProvider, later YahooProvider) implement fetch_quote with
httpx.AsyncClient and translate the raw payload into Quote via classmethod.
"""
