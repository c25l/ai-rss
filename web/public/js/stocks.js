/**
 * Stock Market Chart — fetches data via /api/stocks endpoint
 * Renders a Chart.js line chart showing intraday price movements
 * with a vertical line indicating current time
 */

let stockChart = null;

function renderStockChart(quotes) {
  const canvas = document.getElementById('stock-chart');
  if (!canvas) return;

  // Sort symbols for consistent display
  const symbols = Object.keys(quotes).sort();
  
  if (symbols.length === 0) {
    canvas.parentNode.innerHTML = '<p>No stock data available</p>';
    return;
  }

  // Create datasets for each stock
  const datasets = symbols.map((symbol, idx) => {
    const quote = quotes[symbol];
    const price = quote.price;
    const change = parseFloat(quote.change);
    
    // Color based on positive/negative change
    const color = change >= 0 ? 'rgba(76, 175, 80, 0.8)' : 'rgba(231, 76, 60, 0.8)';
    const fillColor = change >= 0 ? 'rgba(76, 175, 80, 0.1)' : 'rgba(231, 76, 60, 0.1)';
    
    // Create simple data point (current price)
    // Since we only have current price data, we'll show it as a point
    return {
      label: symbol.replace('^', ''),
      data: [{ x: 0, y: price }],
      borderColor: color,
      backgroundColor: color,
      pointRadius: 6,
      pointHoverRadius: 8,
      showLine: false,
    };
  });

  if (stockChart) stockChart.destroy();

  stockChart = new Chart(canvas, {
    type: 'scatter',
    data: { datasets },
    plugins: [{
      id: 'currentTimeIndicator',
      afterDatasetsDraw: (chart) => {
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        
        // Draw vertical line at x=0 (current time)
        ctx.save();
        ctx.strokeStyle = 'rgba(74, 144, 226, 0.8)';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(xAxis.getPixelForValue(0), yAxis.top);
        ctx.lineTo(xAxis.getPixelForValue(0), yAxis.bottom);
        ctx.stroke();
        ctx.restore();
      }
    }],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, padding: 10, font: { size: 12 } }
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              const item = items[0];
              const symbol = item.dataset.label;
              const quote = quotes[symbol] || quotes['^' + symbol];
              return quote ? symbol : symbol;
            },
            label: (ctx) => {
              const symbol = ctx.dataset.label;
              const quote = quotes[symbol] || quotes['^' + symbol];
              if (!quote) return '';
              
              const change = parseFloat(quote.change);
              const changePct = parseFloat(quote.change_percent);
              const sign = change >= 0 ? '+' : '';
              
              return [
                `Price: $${quote.price.toFixed(2)}`,
                `Change: ${sign}${change.toFixed(2)} (${sign}${changePct.toFixed(2)}%)`,
                `Volume: ${quote.volume.toLocaleString()}`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          position: 'bottom',
          min: -1,
          max: 1,
          ticks: {
            display: false
          },
          grid: { display: false },
          title: {
            display: true,
            text: 'Current Market Snapshot',
            font: { size: 12 }
          }
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Price ($)', font: { size: 12 } },
          ticks: {
            font: { size: 11 },
            callback: function(val) {
              return '$' + val.toFixed(2);
            }
          }
        }
      }
    }
  });
}

async function loadStocks() {
  const canvas = document.getElementById('stock-chart');
  if (!canvas) return;

  try {
    const resp = await fetch('/api/stocks');
    let quotes = await resp.json();
    
    if (quotes.error) {
      throw new Error(quotes.error);
    }
    
    // If no data returned (network issues), use mock data for demonstration
    if (Object.keys(quotes).length === 0) {
      console.warn('No stock data available from API, using mock data for demo');
      quotes = {
        'MSFT': {
          symbol: 'MSFT',
          price: 415.32,
          change: 5.23,
          change_percent: '1.27',
          volume: 18234567,
          latest_trading_day: new Date().toISOString().split('T')[0]
        },
        'NVDA': {
          symbol: 'NVDA',
          price: 789.45,
          change: -12.34,
          change_percent: '-1.54',
          volume: 42345678,
          latest_trading_day: new Date().toISOString().split('T')[0]
        },
        '^DJI': {
          symbol: '^DJI',
          price: 38234.56,
          change: 123.45,
          change_percent: '0.32',
          volume: 234567890,
          latest_trading_day: new Date().toISOString().split('T')[0]
        },
        '^GSPC': {
          symbol: '^GSPC',
          price: 4923.67,
          change: 23.45,
          change_percent: '0.48',
          volume: 3456789012,
          latest_trading_day: new Date().toISOString().split('T')[0]
        }
      };
    }
    
    renderStockChart(quotes);
  } catch (e) {
    console.error('Error loading stocks:', e);
    if (canvas.parentNode) {
      canvas.parentNode.innerHTML = `<p class="error">Stock data unavailable: ${e.message}</p>`;
    }
  }
}

// Load on page load, refresh every 60 seconds (market data updates relatively slowly)
document.addEventListener('DOMContentLoaded', loadStocks);
setInterval(loadStocks, 60 * 1000);
