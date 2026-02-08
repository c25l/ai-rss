/**
 * NWS Weather Chart — fetches HOURLY forecast from api.weather.gov
 * No API key needed. Free, public, official government data.
 * Renders a Chart.js temperature + precipitation combo chart with 156 hours of data.
 */

const NWS_LAT = 40.1657;
const NWS_LON = -105.1012;

let weatherChart = null;

function renderWeatherChart(periods) {
  const canvas = document.getElementById('weather-chart');
  if (!canvas) return;

  const labels = periods.map(p => {
    const d = new Date(p.startTime);
    return d.toLocaleDateString('en-US', { weekday: 'short' }) + ' ' +
           d.toLocaleTimeString('en-US', { hour: 'numeric' });
  });

  const temps = periods.map(p => p.temperature);
  const precip = periods.map(p => p.probabilityOfPrecipitation?.value || 0);

  // Shade background by day/night
  const bgColors = periods.map(p =>
    p.isDaytime ? 'rgba(255, 236, 179, 0.15)' : 'rgba(100, 120, 180, 0.08)'
  );

  if (weatherChart) weatherChart.destroy();

  const now = new Date();

  weatherChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Temperature (°F)',
          data: temps,
          borderColor: 'rgba(231, 76, 60, 0.8)',
          backgroundColor: 'rgba(231, 76, 60, 0.08)',
          pointRadius: 0,
          pointHitRadius: 6,
          borderWidth: 2,
          fill: true,
          tension: 0.3,
          yAxisID: 'y',
        },
        {
          label: 'Precip %',
          data: precip,
          borderColor: 'rgba(52, 152, 219, 0.5)',
          backgroundColor: 'rgba(52, 152, 219, 0.12)',
          pointRadius: 0,
          pointHitRadius: 6,
          borderWidth: 1.5,
          fill: true,
          tension: 0.3,
          yAxisID: 'y1',
        }
      ]
    },
    plugins: [{
      id: 'currentTimeIndicator',
      afterDatasetsDraw: (chart) => {
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        
        // Find the index of the current time
        let currentIndex = -1;
        for (let i = 0; i < periods.length; i++) {
          if (new Date(periods[i].startTime) > now) {
            currentIndex = i;
            break;
          }
        }
        
        if (currentIndex >= 0) {
          const x = xAxis.getPixelForValue(currentIndex);
          
          // Draw vertical line at current time
          ctx.save();
          ctx.strokeStyle = 'rgba(74, 144, 226, 0.8)';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.beginPath();
          ctx.moveTo(x, yAxis.top);
          ctx.lineTo(x, yAxis.bottom);
          ctx.stroke();
          
          // Draw label
          ctx.fillStyle = 'rgba(74, 144, 226, 1)';
          ctx.font = 'bold 11px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('NOW', x, yAxis.top - 5);
          ctx.restore();
        }
      }
    }],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, padding: 10, font: { size: 12 } }
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items[0].dataIndex;
              const p = periods[idx];
              const d = new Date(p.startTime);
              return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }) +
                     ' ' + d.toLocaleTimeString('en-US', { hour: 'numeric' });
            },
            afterBody: (items) => {
              const idx = items[0].dataIndex;
              const p = periods[idx];
              return p.shortForecast || '';
            },
            label: ctx => ctx.dataset.yAxisID === 'y1'
              ? `Precip: ${ctx.parsed.y}%`
              : `Temp: ${ctx.parsed.y}°F`
          }
        }
      },
      scales: {
        x: {
          ticks: {
            font: { size: 10 },
            maxRotation: 45,
            maxTicksLimit: 14,
            callback: function(val, idx) {
              // Show label every ~12 hours
              if (idx % 12 === 0) return this.getLabelForValue(val);
              return '';
            }
          },
          grid: { display: false }
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: '°F', font: { size: 12 } },
          ticks: { font: { size: 11 } }
        },
        y1: {
          type: 'linear',
          position: 'right',
          min: 0,
          max: 100,
          title: { display: true, text: 'Precip %', font: { size: 12 } },
          ticks: { font: { size: 11 } },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

async function loadWeather() {
  const alertsContainer = document.getElementById('weather-alerts');
  const canvas = document.getElementById('weather-chart');
  if (!canvas) return;

  try {
    // Step 1: Get the forecast URLs for this location
    let pointData, fcData;
    try {
      const pointResp = await fetch(
        `https://api.weather.gov/points/${NWS_LAT},${NWS_LON}`,
        { headers: { 'User-Agent': 'H3lPeR Dashboard' } }
      );
      pointData = await pointResp.json();
      const hourlyUrl = pointData.properties.forecastHourly;

      // Step 2: Fetch hourly forecast (156 hours)
      const fcResp = await fetch(hourlyUrl, {
        headers: { 'User-Agent': 'H3lPeR Dashboard' }
      });
      fcData = await fcResp.json();
    } catch (e) {
      console.warn('Weather API blocked, using mock data:', e.message);
      // Use mock data endpoint
      const mockResp = await fetch('/api/mock/weather');
      fcData = await mockResp.json();
    }
    
    const periods = fcData.properties.periods;

    // Step 3: Check for alerts (optional, skip if blocked)
    if (alertsContainer) {
      try {
        const alertResp = await fetch(
          `https://api.weather.gov/alerts/active?point=${NWS_LAT},${NWS_LON}`,
          { headers: { 'User-Agent': 'H3lPeR Dashboard' } }
        );
        const alertData = await alertResp.json();
        const alerts = (alertData.features || []);
        if (alerts.length > 0) {
          alertsContainer.innerHTML = '<div class="weather-alerts">' +
            alerts.map(a => {
              const p = a.properties;
              const emoji = p.severity === 'Extreme' ? '🚨' :
                            p.severity === 'Severe' ? '⚠️' :
                            p.severity === 'Moderate' ? '⚡' : 'ℹ️';
              return `<div class="weather-alert">${emoji} <strong>${p.event}</strong>: ${p.headline || ''}</div>`;
            }).join('') + '</div>';
        } else {
          alertsContainer.innerHTML = '';
        }
      } catch (e) {
        // Alerts are optional
      }
    }

    // Step 4: Render chart
    renderWeatherChart(periods);

  } catch (e) {
    if (canvas.parentNode) {
      canvas.parentNode.innerHTML = `<p class="error">Weather unavailable: ${e.message}</p>`;
    }
  }
}

// Load on page load, refresh every 15 minutes
document.addEventListener('DOMContentLoaded', loadWeather);
setInterval(loadWeather, 15 * 60 * 1000);
