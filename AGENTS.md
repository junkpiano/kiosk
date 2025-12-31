# AGENTS

Guidelines for AI agents working in this repository.

## Purpose
Provide a dashboard that shows BTC, stock indices, gold prices, weather, and CPU temperature.

## Development notes
- The main implementation is consolidated in `main.py`.
- The UI returns HTML directly.
- Because it depends on external APIs, return `N/A` when fetches fail.

## Run
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

## Tests
There are no automated tests at the moment.

## Change notes
- Watch for external API spec changes.
- Fetch intervals and cache TTL are managed as constants in `main.py`.
