# Kiosk

A simple trading dashboard powered by FastAPI. It shows BTC, stock indices, gold prices, weather, and CPU temperature.

![Demo](demo.png)

## Requirements
- Python 3.12+
- uv (recommended)

## Setup
```bash
uv sync
```

## Frontend build
```bash
cd frontend
npm install
npm run build
```

## Run
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080` in your browser.

## Deploy
Fabric tasks are defined in `fabfile.py` and use rsync for sync + systemd for service.
```bash
uv run fab -H user@host deploy
```
The deploy task will install `uv` and Node.js (via nvm) on the remote host if missing.

## API
- `GET /api/dashboard`: BTC/indices/gold/temperature/time
- `GET /api/weather`: Current weather in Tokyo

## Notes
Because this depends on external APIs, values may temporarily become `N/A` due to network issues or provider status.
The Svelte UI is served from `frontend/dist` when built; otherwise the legacy inline HTML is used.
