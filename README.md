# tickr

> Async multi-source price tracker CLI — built as the Phase 1 capstone of the AI Engineer Backend Path.

A command-line tool that concurrently fetches crypto and (later) stock prices from
multiple data sources, validates the messy upstream JSON with Pydantic, persists a
local watchlist as a simulated portfolio, and prints sortable performance views.

The project's headline number is the **async vs sync speedup** for refreshing a
multi-symbol watchlist — see the [Benchmark](#benchmark) section.

> **Status**: 🚧 Under active development. See [`../Progress.md`](../Progress.md) for the
> live development dashboard. Current milestone: Stage 1 (data models).

---

## Why this project exists

`tickr` is the integration project for the first three weeks of the Backend Path.
It was deliberately chosen over a CLI expense tracker because:

- **Async needs to do real work.** Concurrent multi-API requests is the canonical
  use case for `asyncio.gather` — a local CRUD app would make `asyncio` decorative.
- **Multiple data sources create a natural Provider abstraction** — inheritance is
  genuinely needed, not forced.
- **Real APIs return messy JSON** — Pydantic earns its keep validating untrusted
  upstream payloads, not just modeling internal state.
- **The `BaseProvider` abstraction is reusable.** It's intentionally designed so
  it can be lifted into a future backtesting / live-trading agent system.

---

## What it does

```bash
# add a holding to your watchlist (symbol, quantity, optional avg cost)
tickr add btc 0.1 28000
tickr add eth 2.0 1800
tickr add sol 50

# show what's in the portfolio
tickr list

# concurrently fetch fresh quotes for every holding
tickr refresh
```

`refresh` is the centerpiece — it spins up one `httpx.AsyncClient` and dispatches
one `fetch_quote(symbol)` coroutine per holding via `asyncio.gather()`. With N
symbols, total wall time is roughly the slowest single request, not N × the
average. That's the whole point of the project.

---

## Architecture

```
                       ┌─────────────────────────┐
                       │       cli.py            │  ← typer commands: add / list / refresh
                       │   (user-facing layer)   │
                       └────────────┬────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │ portfolio.py │    │  storage.py  │    │ providers/   │
        │              │    │              │    │              │
        │ Portfolio    │    │ load/save    │    │ BaseProvider │  ← async ABC
        │  +entries    │    │ portfolio    │    │     │        │
        │  +dunders    │    │  as JSON     │    │     ▼        │
        │              │    │              │    │ CoinGecko    │  ← async HTTP
        │              │    │              │    │   Provider   │
        └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                       ┌─────────────────────────┐
                       │       models.py         │  ← Pydantic: Quote / PortfolioEntry
                       │   (data shape layer)    │
                       │                         │
                       │   exceptions.py         │  ← TickrError tree
                       └─────────────────────────┘
```

**Data flow for `tickr refresh`** (the one that exercises every layer):

1. `cli.py refresh` reads `portfolio.json` via `storage.py` → gets a `Portfolio`
2. For each `PortfolioEntry`, schedule `CoinGeckoProvider.fetch_quote(symbol)`
3. `asyncio.gather(*coros)` runs all of them concurrently inside a single
   `async with httpx.AsyncClient()` block
4. Each provider parses its API's JSON via `Quote.from_api_response(...)` —
   Pydantic raises `ValidationError` if the upstream shape changed
5. HTTP 429 → `RateLimitError`, network/5xx → `ProviderUnavailable`, both
   subclasses of `TickrError` so `cli.py` can catch them in one place
6. `cli.py` sorts the resulting `list[Quote]` (using `Quote.__lt__` by % change)
   and renders a table

---

## Project layout

```
tickr/
├── pyproject.toml          # hatchling, deps, pytest config, console script
├── .gitignore
├── README.md               # ← this file
├── src/tickr/
│   ├── __init__.py         # version
│   ├── __main__.py         # `python -m tickr` entry point
│   ├── cli.py              # typer app: add / list / refresh
│   ├── models.py           # Pydantic: Quote, PortfolioEntry
│   ├── exceptions.py       # TickrError → APIError → RateLimitError / ProviderUnavailable
│   ├── portfolio.py        # Portfolio class with __add__/__len__/__iter__/__repr__
│   ├── storage.py          # JSON load/save, CSV export
│   └── providers/
│       ├── base.py         # BaseProvider (ABC, async fetch_quote)
│       ├── coingecko.py    # crypto provider — MVP
│       └── yahoo.py        # stock provider — Stretch
└── tests/
    ├── conftest.py
    ├── test_models.py      # Pydantic validation, from_api_response
    ├── test_portfolio.py   # dunder methods + sorting
    └── test_providers.py   # async tests with respx-mocked httpx
```

---

## Installation

Requires Python **3.11+**.

```bash
# 1. clone
git clone https://github.com/LovRanRan/tickr.git
cd tickr

# 2. virtual env
python3 -m venv .venv
source .venv/bin/activate

# 3. install in editable mode with dev extras
pip install -e ".[dev]"

# 4. verify
python -m tickr --help
```

---

## Usage

```bash
# add a coin (quantity required, average cost optional)
python -m tickr add btc 0.1 28000

# list current holdings
python -m tickr list

# concurrently refresh quotes
python -m tickr refresh
```

Holdings are persisted to `portfolio.json` in the current working directory.

---

## Tech stack & rationale

| Library | Why this one |
|---|---|
| **httpx** | The async HTTP client of choice in modern Python — same API surface as `requests` but with a real `AsyncClient`. `aiohttp` would also work; httpx is more ergonomic for this use case. |
| **pydantic** v2 | Validates messy upstream JSON, not just internal data. v2 is faster than v1 and uses `field_validator` (note: not the v1 `validator`). |
| **typer** | Type-hint-driven CLI built on Click. Auto-generates `--help` from function signatures + docstrings, so the CLI stays in lockstep with the type annotations the rest of the codebase uses. |
| **pytest + pytest-asyncio + respx** | `pytest-asyncio` lets test functions be `async def`. `respx` mocks `httpx` at the transport level so tests don't hit the real CoinGecko API. |

---

## Async vs sync benchmark <a id="benchmark"></a>

The single most important number this project produces. Refresh N symbols, measure
wall time for sequential vs concurrent execution.

🚧 **Numbers pending — filled in during Stage 5.** Expected shape:

```
Refreshing 10 symbols against CoinGecko:
  sequential (await one at a time):   ~2.1 s
  concurrent (asyncio.gather):        ~0.25 s
  speedup:                            ~8.4×
```

The sequential baseline is generated by an explicit `for symbol in symbols: await
provider.fetch_quote(symbol)` loop; the concurrent version is the production code
path. Numbers will vary with network conditions; the ratio is the interesting bit.

---

## Skills exercised (Phase 1 mapping)

| Skill | Where it lands |
|---|---|
| OOP classes + class variables | `Quote`, `Asset`, `Portfolio`, `BaseProvider` |
| Inheritance | `BaseProvider` → `CoinGeckoProvider`, `YahooProvider` |
| `classmethod` | `Quote.from_api_response(data)`, `Portfolio.from_json(path)` |
| Dunder methods | `Portfolio.__add__`, `__len__`, `__iter__`, `__repr__`; `Quote.__lt__` |
| asyncio | `asyncio.gather()` for parallel API calls; `async with httpx.AsyncClient()` |
| Type hints | Full coverage across function signatures and return types |
| Pydantic | `Quote`, `PortfolioEntry` validating API responses with `field_validator` |
| Exception handling | Custom tree: `TickrError` → `APIError` → `RateLimitError` / `ProviderUnavailable` |
| File I/O | JSON portfolio persistence, CSV export |
| Unit testing | `pytest` + `pytest-asyncio` + `respx` for mocking async HTTP |
| Git/GitHub | Stage-by-stage commits, Actions running pytest (Stretch) |

---

## Roadmap

Tracked in detail in [`../Progress.md`](../Progress.md). High-level:

- ✅ **Stage 0** — project skeleton, CLI stubs, dependencies installed
- 🟡 **Stage 1** — `models.py` + `exceptions.py` (Pydantic data shapes)
- ⬜ **Stage 2** — `BaseProvider` + `CoinGeckoProvider` (the async core)
- ⬜ **Stage 3** — `Portfolio` + `storage.py` (OOP + persistence)
- ⬜ **Stage 4** — wire everything through `cli.py` end-to-end
- ⬜ **Stage 5** — pytest suite, README benchmark numbers, Git polish
- ⬜ **Stretch** — Yahoo provider, `rich` table output, GitHub Actions CI

---

## License

MIT
