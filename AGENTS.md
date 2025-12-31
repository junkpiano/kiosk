# AGENTS

Guidelines for AI agents working in this repository.

## Purpose
Provide a dashboard that shows BTC, stock indices, gold prices, weather, and CPU temperature.

## Development notes
- The main implementation is consolidated in `main.py`.
- The UI is built with Svelte (Vite) in `frontend/` and compiled to `frontend/dist`.
- `main.py` serves `frontend/dist/index.html` when present and falls back to the legacy inline HTML when not built.
- Because it depends on external APIs, return `N/A` when fetches fail.

## Requirements
- Python 3.12+
- uv (recommended)

## Setup
```bash
uv sync
```

## Run
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

## Frontend build
```bash
cd frontend
npm install
npm run build
```

## API
- `GET /api/dashboard`: BTC/indices/gold/temperature/time
- `GET /api/weather`: Current weather in Tokyo

## Tests
There are no automated tests at the moment.

## Change notes
- Watch for external API spec changes.
- Fetch intervals and cache TTL are managed as constants in `main.py`.
