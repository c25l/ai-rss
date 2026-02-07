/**
 * SWPC Kp-Index Chart — fetches from NOAA SWPC JSON API
 * Planetary K-index forecast: observed + predicted, 3-hour intervals
 * Bars colored by geomagnetic storm level (G1–G5)
 */

const SWPC_KP_URL = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json';

let kpChart = null;

// Kp color scale matching NOAA conventions
function kpColor(kp) {
  if (kp >= 9) return 'rgba(200, 0, 0, 0.9)';       // G5 - Extreme
  if (kp >= 8) return 'rgba(230, 30, 30, 0.9)';      // G4 - Severe
  if (kp >= 7) return 'rgba(255, 100, 0, 0.9)';      // G3 - Strong
  if (kp >= 6) return 'rgba(255, 165, 0, 0.9)';      // G2 - Moderate
  if (kp >= 5) return 'rgba(255, 200, 0, 0.9)';      // G1 - Minor
  if (kp >= 4) return 'rgba(120, 180, 60, 0.8)';     // Active
  return 'rgba(76, 175, 80, 0.7)';                    // Quiet
}

function kpBorderColor(kp) {
  if (kp >= 5) return 'rgba(180, 0, 0, 1)';
  return 'rgba(56, 142, 60, 1)';
}

function renderKpChart(data) {
  const canvas = document.getElementById('kp-chart');
  if (!canvas) return;

  // Skip header row
  const rows = data.slice(1);

  const labels = rows.map(r => {
    const d = new Date(r[0] + 'Z');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
           d.toLocaleTimeString('en-US', { hour: 'numeric', hour12: true });
  });

  const kpValues = rows.map(r => parseFloat(r[1]));
  const bgColors = kpValues.map(kp => kpColor(kp));
  const borderColors = kpValues.map(kp => kpBorderColor(kp));
  const isObserved = rows.map(r => r[2] === 'observed');

  if (kpChart) kpChart.destroy();

  kpChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Kp Index',
        data: kpValues,
        backgroundColor: bgColors,
        borderColor: borderColors,
        borderWidth: rows.map(r => r[2] === 'predicted' ? 1 : 0),
        borderDash: [],
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items[0].dataIndex;
              const r = rows[idx];
              const d = new Date(r[0] + 'Z');
              return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) +
                     ' ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
            },
            label: (ctx) => {
              const idx = ctx.dataIndex;
              const r = rows[idx];
              const kp = parseFloat(r[1]);
              const type = r[2]; // observed, estimated, predicted
              const scale = r[3] || (kp >= 5 ? `G${Math.min(Math.floor(kp) - 4, 5)}` : 'Quiet');
              return `Kp: ${kp.toFixed(1)} (${type}) — ${scale}`;
            }
          }
        },
        annotation: undefined
      },
      scales: {
        x: {
          ticks: {
            font: { size: 10 },
            maxRotation: 45,
            maxTicksLimit: 12,
            callback: function(val, idx) {
              // Show every 8th label (~daily)
              if (idx % 8 === 0) return this.getLabelForValue(val);
              return '';
            }
          },
          grid: { display: false }
        },
        y: {
          min: 0,
          max: 9,
          title: { display: true, text: 'Kp', font: { size: 12 } },
          ticks: {
            font: { size: 11 },
            stepSize: 1,
            callback: function(val) {
              if (val === 5) return '5 (G1)';
              if (val === 6) return '6 (G2)';
              if (val === 7) return '7 (G3)';
              if (val === 8) return '8 (G4)';
              if (val === 9) return '9 (G5)';
              return val;
            }
          }
        }
      }
    }
  });
}

async function loadSpaceWeather() {
  const canvas = document.getElementById('kp-chart');
  if (!canvas) return;

  try {
    const resp = await fetch(SWPC_KP_URL);
    const data = await resp.json();
    renderKpChart(data);
  } catch (e) {
    if (canvas.parentNode) {
      canvas.parentNode.innerHTML = `<p class="error">Space weather unavailable: ${e.message}</p>`;
    }
  }
}

// Load on page load, refresh every 15 minutes
document.addEventListener('DOMContentLoaded', loadSpaceWeather);
setInterval(loadSpaceWeather, 15 * 60 * 1000);
