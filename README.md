# tickr

> Async multi-source price tracker CLI — Phase 1 mini-project for the AI Engineer Backend Path.

A command-line tool that concurrently fetches crypto (and later stock) prices from
multiple data sources, maintains a local watchlist / simulated portfolio, and shows
sortable performance views.

The README will be filled in during **Stage 5** with:

- Install steps (`pip install -e ".[dev]"`)
- Usage examples (`tickr add btc 0.1`, `tickr list`, `tickr refresh`)
- **Async vs sync benchmark numbers** (the headline number this project exists to produce)
- Project layout and skill mapping

For now, see [`../Progress.md`](../Progress.md) for the live development dashboard
and [`../tickr-project-plan.md`](../tickr-project-plan.md) for the design document.

## Quick start (during development)

```bash
# from the tickr/ directory
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m tickr --help
```
