"""Custom exception tree — Stage 1.

TickrError                  (base for everything tickr raises)
├── APIError                (anything coming back wrong from a provider)
│   ├── RateLimitError      (HTTP 429 — retry with backoff)
│   └── ProviderUnavailable (network failure, 5xx, parse error)
"""
