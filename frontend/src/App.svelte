<script>
  import { onMount } from 'svelte';

  const weatherCodes = {
    0: 'Clear',
    1: 'Mainly clear',
    2: 'Partly cloudy',
    3: 'Overcast',
    45: 'Fog',
    48: 'Rime fog',
    51: 'Light drizzle',
    53: 'Moderate drizzle',
    55: 'Dense drizzle',
    61: 'Slight rain',
    63: 'Moderate rain',
    65: 'Heavy rain',
    71: 'Slight snow',
    73: 'Moderate snow',
    75: 'Heavy snow',
    80: 'Rain showers',
    81: 'Heavy showers',
    82: 'Violent showers',
    95: 'Thunderstorm',
    96: 'Thunderstorm + hail',
    99: 'Thunderstorm + heavy hail'
  };

  let dashboard = {
    btc: 'N/A',
    sp500: 'N/A',
    nikkei225: 'N/A',
    gold_jpy: 'N/A',
    temp: 'N/A',
    time: 'N/A'
  };

  let weather = {
    temperature: 'N/A',
    weathercode: 'N/A',
    windspeed: 'N/A',
    time: 'N/A'
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
    updateWeather();
    updateHeaderTime();

    const dashboardTimer = setInterval(updateDashboard, 30000);
    const weatherTimer = setInterval(updateWeather, 3600000);
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
</script>

<div class="dashboard">
  <h1 id="time-header">{headerTime}</h1>
  <div id="metrics">
    <div class="metric weather">
      ☁️ 東京の天気: {weatherCondition}<br />
      🌡️ {weatherTempText}<br />
      💨 {weatherWindText}<br />
      <span class="weather-time">🕒 {weatherTimeText} 時点</span>
    </div>
    <div class="metric btc">₿ ビットコイン: ￥{btcText}</div>
    <div class="metric sp500">📈 S&P 500: {sp500Text}</div>
    <div class="metric nikkei">🇯🇵 日経平均: {nikkeiText}</div>
    <div class="metric gold">🪙 金（円）: {goldText}</div>
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

  .temp {
    border-color: #ff1493;
    background: rgba(255, 20, 147, 0.1);
  }

  .weather {
    border-color: #32cd32;
    background: rgba(50, 205, 50, 0.1);
  }

  .weather-time {
    font-size: 0.8em;
    opacity: 0.8;
  }

  @media (max-height: 520px) {
    :global(body) {
      padding: 6px 8px;
    }

    .metric {
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
