"""Custom exception tree — Stage 1.

TickrError                  (base for everything tickr raises)
├── APIError                (anything coming back wrong from a provider)
│   ├── RateLimitError      (HTTP 429 — retry with backoff)
│   └── ProviderUnavailable (network failure, 5xx, parse error)
"""


class TickrError(Exception):
    pass


class APIError(TickrError):
    pass


class RateLimitError(APIError):
    """Raised when a provider returns HTTP 429."""
    pass


class ProviderUnavailable(APIError):
    pass