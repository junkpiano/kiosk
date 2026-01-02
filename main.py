from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import psutil
from datetime import datetime
from zoneinfo import ZoneInfo
import time
from pathlib import Path

try:
    from geopy.geocoders import Nominatim
except Exception:
    Nominatim = None

app = FastAPI(title="Trading Dashboard")

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
DIST_INDEX = DIST_DIR / "index.html"
DIST_ASSETS = DIST_DIR / "assets"

if DIST_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=DIST_ASSETS), name="assets")

# -----------------------------
# Simple in-memory cache (1 hour)
# -----------------------------
CACHE_TTL_SECONDS = 60 * 60
_cache_store = {}
_geolocator = Nominatim(user_agent="kiosk_dashboard") if Nominatim else None

def _get_cache(key):
    cached = _cache_store.get(key)
    if not cached:
        return None
    if time.time() - cached["ts"] > CACHE_TTL_SECONDS:
        return None
    return cached["value"]

def _set_cache(key, value):
    _cache_store[key] = {"value": value, "ts": time.time()}


# -----------------------------
# Index Fetcher (Stooq)
# -----------------------------
def fetch_index(symbol: str):
    """
    Stooq symbols:
      ^spx = S&P500
      ^nkx = Nikkei 225
    """
    cache_key = f"stooq:{symbol}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        r = requests.get(
            "https://stooq.com/q/l/",
            params={
                "s": symbol,
                "f": "sd2t2ohlcv",
                "h": "",
                "e": "csv",
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        r.raise_for_status()

        lines = [line.strip() for line in r.text.splitlines() if line.strip()]
        # Header:
        # Symbol,Date,Time,Open,High,Low,Close,Volume
        if len(lines) >= 2:
            data = lines[1].split(",")
            close_price = data[6]  # Close
            if close_price.upper() not in ("N/A", "N/D"):
                value = float(close_price)
                _set_cache(cache_key, value)
                return value
    except Exception:
        pass

    # Fallback: use last available daily close (helps on holidays/market closed)
    try:
        r = requests.get(
            "https://stooq.com/q/d/l/",
            params={"s": symbol, "i": "d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        r.raise_for_status()
        lines = [line.strip() for line in r.text.splitlines() if line.strip()]
        # Header:
        # Date,Open,High,Low,Close,Volume
        if len(lines) >= 2:
            last = lines[-1].split(",")
            close_price = last[4]
            if close_price.upper() not in ("N/A", "N/D"):
                value = float(close_price)
                _set_cache(cache_key, value)
                return value
    except Exception:
        pass

    return "N/A"

def fetch_location_name(latitude: float | None, longitude: float | None):
    if latitude is None or longitude is None:
        return "東京"

    if _geolocator is None:
        return "東京"

    cache_key = f"geocode:{latitude:.4f},{longitude:.4f}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        location = _geolocator.reverse(
            (latitude, longitude),
            language="ja",
            zoom=10,
            addressdetails=True,
            timeout=5,
        )
        if location and location.raw and isinstance(location.raw, dict):
            address = location.raw.get("address", {})
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            )
            admin1 = address.get("state") or address.get("province")
            if admin1 and city:
                value = f"{admin1} {city}"
                _set_cache(cache_key, value)
                return value
    except Exception:
        pass

    return "東京"

def fetch_weather(latitude: float | None = None, longitude: float | None = None):
    lat = latitude if latitude is not None else 35.6762
    lon = longitude if longitude is not None else 139.6503
    cache_key = f"weather:{lat:.4f},{lon:.4f}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    location_name = fetch_location_name(latitude, longitude)

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "timezone": "Asia/Tokyo",
            },
            timeout=5,
        )
        r.raise_for_status()
        data = r.json().get("current_weather", {})
        value = {
            "temperature": data.get("temperature", "N/A"),
            "weathercode": data.get("weathercode", "N/A"),
            "windspeed": data.get("windspeed", "N/A"),
            "time": data.get("time", "N/A"),
            "location": location_name,
        }
        _set_cache(cache_key, value)
        return value
    except Exception:
        return {
            "temperature": "N/A",
            "weathercode": "N/A",
            "windspeed": "N/A",
            "time": "N/A",
            "location": location_name,
        }


# -----------------------------
# API Endpoint
# -----------------------------
@app.get("/api/dashboard")
async def get_dashboard():
    # BTC price (JPY)
    btc_cache_key = "coingecko:btc:jpy"
    try:
        cached_btc = _get_cache(btc_cache_key)
        if cached_btc is not None:
            btc = cached_btc
        else:
            btc = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "jpy"},
                timeout=5,
            ).json()["bitcoin"]["jpy"]
            _set_cache(btc_cache_key, btc)
    except Exception:
        btc = "N/A"

    # Indexes
    sp500 = fetch_index("^spx")
    nikkei225 = fetch_index("^nkx")

    # Gold prices
    gold_jpy = fetch_index("xaujpy")

    # USD/JPY
    usd_jpy = fetch_index("usdjpy")

    # CPU temperature
    try:
        temp_data = psutil.sensors_temperatures()["cpu_thermal"][0].current
        temp = round(temp_data, 1)
    except Exception:
        temp = "N/A"

    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))

    return {
        "btc": btc,
        "sp500": sp500,
        "nikkei225": nikkei225,
        "gold_jpy": gold_jpy,
        "usd_jpy": usd_jpy,
        "temp": temp,
        "time": now_jst.strftime("%Y-%m-%d %H:%M:%S JST"),
    }

@app.get("/api/weather")
async def get_weather(lat: float | None = None, lon: float | None = None):
    return fetch_weather(latitude=lat, longitude=lon)


@app.get("/")
async def dashboard():
    if DIST_INDEX.exists():
        return FileResponse(DIST_INDEX)
    
    return HTMLResponse("""
    <html>
      <head><title>Trading Dashboard</title></head>
      <body>
        <h1>Trading Dashboard</h1>
        <p>Now building...</p>
      </body>
    </html>
    """)


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn  
    uvicorn.run(app, host="0.0.0.0", port=8080)
