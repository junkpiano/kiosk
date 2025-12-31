from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import psutil
from datetime import datetime
from zoneinfo import ZoneInfo
import time

app = FastAPI(title="Trading Dashboard")

# -----------------------------
# Simple in-memory cache (1 hour)
# -----------------------------
CACHE_TTL_SECONDS = 60 * 60
_cache_store = {}

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

def fetch_weather():
    cache_key = "weather:tokyo"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 35.6762,
                "longitude": 139.6503,
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
        }
        _set_cache(cache_key, value)
        return value
    except Exception:
        return {
            "temperature": "N/A",
            "weathercode": "N/A",
            "windspeed": "N/A",
            "time": "N/A",
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
        "temp": temp,
        "time": now_jst.strftime("%Y-%m-%d %H:%M:%S JST"),
    }

@app.get("/api/weather")
async def get_weather():
    return fetch_weather()


# -----------------------------
# Dashboard HTML
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: linear-gradient(135deg, #000, #1a1a1a);
            color: #0f0;
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: clamp(8px, 1.5vh, 16px) clamp(10px, 4vw, 32px);
        }

        .dashboard {
            text-align: center;
            width: min(92vw, 900px);
            max-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: clamp(6px, 1.2vh, 12px);
        }

        h1 {
            margin-bottom: clamp(6px, 1.2vh, 12px);
            font-size: clamp(1.1rem, 3.2vh, 2.2rem);
            line-height: 1.1;
        }

        #metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: clamp(6px, 1.2vh, 12px);
        }

        .metric {
            font-size: clamp(1.1rem, 3.2vh, 2.4rem);
            margin: 0;
            padding: clamp(8px, 1.6vh, 14px);
            border: 2px solid;
            border-radius: 15px;
            line-height: 1.1;
        }

        .btc {
            border-color: #f7931a;
            background: rgba(247,147,26,0.1);
        }

        .sp500 {
            border-color: #1e90ff;
            background: rgba(30,144,255,0.1);
        }

        .nikkei {
            border-color: #ff4500;
            background: rgba(255,69,0,0.1);
        }

        .gold {
            border-color: #ffd700;
            background: rgba(255,215,0,0.12);
        }

        .temp {
            border-color: #ff1493;
            background: rgba(255,20,147,0.1);
        }

        .weather {
            border-color: #32cd32;
            background: rgba(50,205,50,0.1);
        }

        .weather-time {
            font-size: 0.8em;
            opacity: 0.8;
        }

        .time {
            margin-top: clamp(6px, 1.2vh, 12px);
            font-size: clamp(0.85rem, 2.2vh, 1.2rem);
            opacity: 0.8;
        }

        @media (max-height: 520px) {
            body { padding: 6px 8px; }
            .metric { border-width: 1px; border-radius: 10px; }
        }

        @media (max-width: 780px) {
            #metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }

        @media (max-width: 520px) {
            #metrics { grid-template-columns: 1fr; }
        }
    </style>
</head>

<body>
    <div class="dashboard">
        <h1 id="time-header">--:--:--</h1>
        <div id="metrics">Loading...</div>
    </div>

    <script>
        const weatherCodes = {
            0: "Clear",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Heavy showers",
            82: "Violent showers",
            95: "Thunderstorm",
            96: "Thunderstorm + hail",
            99: "Thunderstorm + heavy hail"
        };

        async function updateWeather() {
            try {
                const res = await fetch('/api/weather');
                const data = await res.json();
                const condition = weatherCodes[data.weathercode] || "不明";
                const tempText = typeof data.temperature === 'number' ? `${data.temperature}°C` : data.temperature;
                const windText = typeof data.windspeed === 'number' ? `${data.windspeed} m/s` : data.windspeed;
                const timeText = data.time !== "N/A" ? data.time.replace("T", " ") : data.time;

                const weatherEl = document.getElementById('weather');
                if (!weatherEl) {
                    return;
                }

                weatherEl.innerHTML = `
                    ☁️ 東京の天気: ${condition}<br>
                    🌡️ ${tempText}<br>
                    💨 ${windText}<br>
                    <span class="weather-time">🕒 ${timeText} 時点</span>
                `;
            } catch (e) {
                console.error("Weather update failed", e);
            }
        }

        async function updateDashboard() {
            try {
                const res = await fetch('/api/dashboard');
                const data = await res.json();

                const formatCurrency = (value, symbol) =>
                    `${symbol}${typeof value === 'number' ? value.toLocaleString() : value}`;

                document.getElementById('metrics').innerHTML = `
                    <div class="metric weather" id="weather">Loading...</div>
                    <div class="metric btc">
                        ₿ ビットコイン: ￥${typeof data.btc === 'number' ? data.btc.toLocaleString() : data.btc}
                    </div>
                    <div class="metric sp500">
                        📈 S&P 500: ${formatCurrency(data.sp500, '＄')}
                    </div>
                    <div class="metric nikkei">
                        🇯🇵 日経平均: ${formatCurrency(data.nikkei225, '￥')}
                    </div>
                    <div class="metric gold">
                        🪙 金（円）: ${formatCurrency(data.gold_jpy, '￥')}
                    </div>
                    <div class="metric temp">
                        🌡️ CPU温度: ${data.temp}°C
                    </div>
                `;
                await updateWeather();
            } catch (e) {
                console.error("Dashboard update failed", e);
            }
        }

        function updateHeaderTime() {
            const now = new Date();
            const pad2 = (value) => String(value).padStart(2, '0');
            const dateText = [
                now.getFullYear(),
                pad2(now.getMonth() + 1),
                pad2(now.getDate())
            ].join('/');
            const timeText = [
                pad2(now.getHours()),
                pad2(now.getMinutes()),
                pad2(now.getSeconds())
            ].join(':');
            document.getElementById('time-header').textContent = `🕒 ${dateText} ${timeText}`;
        }

        updateDashboard();
        updateWeather();
        updateHeaderTime();
        setInterval(updateWeather, 3600000);
        setInterval(updateDashboard, 30000);
        setInterval(updateHeaderTime, 1000);
    </script>
</body>
</html>
"""


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
