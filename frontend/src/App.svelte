<script>
  import { onMount } from 'svelte';

  const weatherCodes = {
    0: '快晴', // Clear
    1: 'おおむね晴れ', // Mainly clear
    2: '一部曇り', // Partly cloudy
    3: '曇り', // Overcast
    45: '霧', // Fog
    48: '着氷性の霧', // Rime fog
    51: '弱い霧雨', // Light drizzle
    53: '霧雨', // Moderate drizzle
    55: '強い霧雨', // Dense drizzle
    61: '弱い雨', // Slight rain
    63: '雨', // Moderate rain
    65: '強い雨', // Heavy rain
    71: '弱い雪', // Slight snow
    73: '雪', // Moderate snow
    75: '強い雪', // Heavy snow
    80: 'にわか雨', // Rain showers
    81: '強いにわか雨', // Heavy showers
    82: '激しいにわか雨', // Violent showers
    95: '雷雨', // Thunderstorm
    96: '雷雨（雹）', // Thunderstorm + hail
    99: '激しい雷雨（雹）' // Thunderstorm + heavy hail
  };

  let dashboard = {
    btc: 'N/A',
    sp500: 'N/A',
    nikkei225: 'N/A',
    gold_jpy: 'N/A',
    usd_jpy: 'N/A',
    temp: 'N/A',
    time: 'N/A'
  };

  let weather = {
    temperature: 'N/A',
    weathercode: 'N/A',
    windspeed: 'N/A',
    time: 'N/A',
    location: '東京'
  };

  let headerTime = '--:--:--';

  const formatCurrency = (value, symbol) =>
    `${symbol}${typeof value === 'number' ? value.toLocaleString() : value}`;

  const updateDashboard = async () => {
    try {
      const res = await fetch('/api/dashboard');
      dashboard = await res.json();
    } catch (error) {
      console.error('Dashboard update failed', error);
    }
  };

  const updateWeather = async () => {
    try {
      const res = await fetch('/api/weather');
      weather = await res.json();
    } catch (error) {
      console.error('Weather update failed', error);
    }
  };

  const getCurrentPosition = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation unsupported'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 5000,
        maximumAge: 600000
      });
    });

  const updateWeatherWithLocation = async () => {
    try {
      const pos = await getCurrentPosition();
      const { latitude, longitude } = pos.coords;
      const res = await fetch(`/api/weather?lat=${latitude}&lon=${longitude}`);
      const data = await res.json();
      if (data.temperature === 'N/A') {
        await updateWeather();
        return;
      }
      weather = data;
    } catch (error) {
      await updateWeather();
    }
  };

  const updateHeaderTime = () => {
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
    headerTime = `🕒 ${dateText} ${timeText}`;
  };

  onMount(() => {
    updateDashboard();
    updateWeatherWithLocation();
    updateHeaderTime();

    const dashboardTimer = setInterval(updateDashboard, 30000);
    const weatherTimer = setInterval(updateWeatherWithLocation, 3600000);
    const clockTimer = setInterval(updateHeaderTime, 1000);

    return () => {
      clearInterval(dashboardTimer);
      clearInterval(weatherTimer);
      clearInterval(clockTimer);
    };
  });

  $: btcText = typeof dashboard.btc === 'number' ? dashboard.btc.toLocaleString() : dashboard.btc;
  $: sp500Text = formatCurrency(dashboard.sp500, '＄');
  $: nikkeiText = formatCurrency(dashboard.nikkei225, '￥');
  $: goldText = formatCurrency(dashboard.gold_jpy, '￥');
  $: usdJpyText = formatCurrency(dashboard.usd_jpy, '￥');
  $: tempText = typeof dashboard.temp === 'number' ? `${dashboard.temp}°C` : dashboard.temp;
  $: weatherCondition =
    typeof weather.weathercode === 'number'
      ? weatherCodes[weather.weathercode] || '不明'
      : weather.weathercode;
  $: weatherTempText =
    typeof weather.temperature === 'number' ? `${weather.temperature}°C` : weather.temperature;
  $: weatherWindText =
    typeof weather.windspeed === 'number' ? `${weather.windspeed} m/s` : weather.windspeed;
  $: weatherTimeText =
    weather.time !== 'N/A' ? weather.time.replace('T', ' ') : weather.time;
  $: weatherLocation = weather.location || '東京';
</script>

<div class="dashboard">
  <h1 id="time-header">{headerTime}</h1>
  <section class="weather-section">
    <div class="weather-card">
      <div class="weather-main">☁️ {weatherLocation}</div>
      <div>{weatherCondition}</div>
      <div>🌡️ {weatherTempText}</div>
      <div>💨 {weatherWindText}</div>
      <div class="weather-time">🕒 {weatherTimeText} 時点</div>
    </div>
  </section>
  <div id="metrics">
    <div class="metric nikkei">🇯🇵 日経平均: {nikkeiText}</div>
    <div class="metric sp500">📈 S&P 500: {sp500Text}</div>
    <div class="metric gold">🪙 金（円）: {goldText}</div>
    <div class="metric fx">💱 ドル円: {usdJpyText}</div>
    <div class="metric btc">₿ ビットコイン: ￥{btcText}</div>
    <div class="metric temp">🌡️ CPU温度: {tempText}</div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    background: linear-gradient(135deg, #000, #1a1a1a);
    color: #0f0;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: clamp(8px, 1.5vh, 16px) clamp(10px, 4vw, 32px);
  }

  :global(*) {
    box-sizing: border-box;
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

  .metric,
  .weather-card,
  .fixed-temp {
    font-size: clamp(1.1rem, 3.2vh, 2.4rem);
    margin: 0;
    padding: clamp(8px, 1.6vh, 14px);
    border: 2px solid;
    border-radius: 15px;
    line-height: 1.1;
  }

  .btc {
    border-color: #f7931a;
    background: rgba(247, 147, 26, 0.1);
  }

  .sp500 {
    border-color: #1e90ff;
    background: rgba(30, 144, 255, 0.1);
  }

  .nikkei {
    border-color: #ff4500;
    background: rgba(255, 69, 0, 0.1);
  }

  .gold {
    border-color: #ffd700;
    background: rgba(255, 215, 0, 0.12);
  }

  .fx {
    border-color: #00ced1;
    background: rgba(0, 206, 209, 0.12);
  }

  .temp,
  .fixed-temp {
    border-color: #ff1493;
    background: rgba(255, 20, 147, 0.1);
  }

  .weather-time {
    font-size: 0.8em;
    opacity: 0.8;
  }

  .weather-section h2 {
    font-size: clamp(0.95rem, 2.6vh, 1.6rem);
    margin-bottom: clamp(4px, 0.8vh, 8px);
  }

  .weather-card {
    border-color: #32cd32;
    background: rgba(50, 205, 50, 0.1);
    display: grid;
    gap: clamp(4px, 0.8vh, 8px);
  }

  .weather-main {
    font-size: clamp(1.2rem, 3.4vh, 2.6rem);
  }

  .fixed-temp {
    position: fixed;
    right: clamp(10px, 2vw, 24px);
    bottom: clamp(10px, 2vh, 24px);
    font-size: clamp(0.95rem, 2.4vh, 1.6rem);
    z-index: 10;
  }

  @media (max-height: 520px) {
    :global(body) {
      padding: 6px 8px;
    }

    .metric,
    .weather-card,
    .fixed-temp {
      border-width: 1px;
      border-radius: 10px;
    }
  }

  @media (max-width: 780px) {
    #metrics {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 520px) {
    #metrics {
      grid-template-columns: 1fr;
    }
  }
</style>
