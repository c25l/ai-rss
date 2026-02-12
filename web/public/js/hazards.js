/**
 * Natural Hazards Map — interactive Leaflet map showing live hazard data
 *
 * Data sources (all free, no API keys):
 *   - USGS Earthquake Feed: M2.5+ earthquakes from the last 7 days
 *   - NASA EONET v3: Active natural events (wildfires, storms, volcanoes, etc.)
 *   - NWS Active Alerts: Weather warnings/watches near configured location
 *
 * Renders markers color-coded by hazard type with popups showing details.
 */

const HAZARDS_NWS_LAT = 40.1657;
const HAZARDS_NWS_LON = -105.1012;

const USGS_QUAKE_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson';
const EONET_URL = 'https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100';
const NWS_ALERTS_URL = `https://api.weather.gov/alerts/active?point=${HAZARDS_NWS_LAT},${HAZARDS_NWS_LON}`;

let hazardMap = null;

// EONET category → display config
const EONET_CATEGORIES = {
  wildfires:    { emoji: '🔥', color: '#e74c3c', label: 'Wildfire' },
  severeStorms: { emoji: '🌀', color: '#8e44ad', label: 'Severe Storm' },
  volcanoes:    { emoji: '🌋', color: '#d35400', label: 'Volcano' },
  seaLakeIce:   { emoji: '🧊', color: '#3498db', label: 'Sea/Lake Ice' },
  floods:       { emoji: '🌊', color: '#2980b9', label: 'Flood' },
  landslides:   { emoji: '⛰️', color: '#795548', label: 'Landslide' },
  snow:         { emoji: '❄️', color: '#90caf9', label: 'Snow' },
  dustHaze:     { emoji: '🌫️', color: '#bcaaa4', label: 'Dust/Haze' },
  earthquakes:  { emoji: '🔴', color: '#c0392b', label: 'Earthquake' },
};

function getEonetConfig(categoryId) {
  return EONET_CATEGORIES[categoryId] || { emoji: '⚠️', color: '#f39c12', label: categoryId };
}

function quakeColor(mag) {
  if (mag >= 7) return '#7f0000';
  if (mag >= 6) return '#b71c1c';
  if (mag >= 5) return '#e53935';
  if (mag >= 4) return '#ff9800';
  if (mag >= 3) return '#ffc107';
  return '#8bc34a';
}

function quakeRadius(mag) {
  return Math.max(4, Math.min(mag * 3, 24));
}

function initMap() {
  const container = document.getElementById('hazard-map');
  if (!container || hazardMap) return;

  hazardMap = L.map('hazard-map').setView([HAZARDS_NWS_LAT, HAZARDS_NWS_LON], 4);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(hazardMap);

  // Home marker
  L.circleMarker([HAZARDS_NWS_LAT, HAZARDS_NWS_LON], {
    radius: 6, color: '#2196f3', fillColor: '#2196f3', fillOpacity: 0.8, weight: 2,
  }).addTo(hazardMap).bindPopup('<strong>📍 Home Location</strong>');
}

// ── Earthquake layer ─────────────────────────────────────────────────────────

async function loadEarthquakes() {
  const status = document.getElementById('quake-status');
  try {
    const resp = await fetch(USGS_QUAKE_URL);
    const data = await resp.json();
    const features = data.features || [];

    features.forEach(f => {
      const [lon, lat, depth] = f.geometry.coordinates;
      const mag = f.properties.mag;
      const place = f.properties.place || 'Unknown';
      const time = new Date(f.properties.time).toLocaleString();

      L.circleMarker([lat, lon], {
        radius: quakeRadius(mag),
        color: quakeColor(mag),
        fillColor: quakeColor(mag),
        fillOpacity: 0.6,
        weight: 1,
      }).addTo(hazardMap).bindPopup(
        `<strong>🔴 M${mag.toFixed(1)} Earthquake</strong><br>` +
        `${place}<br>` +
        `Depth: ${depth.toFixed(1)} km<br>` +
        `<small>${time}</small>`
      );
    });

    if (status) status.textContent = `${features.length} earthquakes (M2.5+ past 7 days)`;
  } catch (e) {
    if (status) status.textContent = 'Earthquake data unavailable';
  }
}

// ── NASA EONET layer (wildfires, storms, volcanoes, etc.) ────────────────────

async function loadEONET() {
  const status = document.getElementById('eonet-status');
  try {
    const resp = await fetch(EONET_URL);
    const data = await resp.json();
    const events = data.events || [];

    let counts = {};
    events.forEach(ev => {
      const catId = (ev.categories && ev.categories[0]) ? ev.categories[0].id : 'unknown';
      const cfg = getEonetConfig(catId);
      counts[cfg.label] = (counts[cfg.label] || 0) + 1;

      // Use the most recent geometry
      const geom = ev.geometry && ev.geometry[ev.geometry.length - 1];
      if (!geom || !geom.coordinates) return;

      const [lon, lat] = geom.coordinates;
      const date = geom.date ? new Date(geom.date).toLocaleDateString() : '';

      L.circleMarker([lat, lon], {
        radius: 7,
        color: cfg.color,
        fillColor: cfg.color,
        fillOpacity: 0.7,
        weight: 1,
      }).addTo(hazardMap).bindPopup(
        `<strong>${cfg.emoji} ${cfg.label}</strong><br>` +
        `${ev.title}<br>` +
        (date ? `<small>${date}</small>` : '')
      );
    });

    if (status) {
      const parts = Object.entries(counts).map(([k, v]) => `${v} ${k.toLowerCase()}`);
      status.textContent = parts.length ? parts.join(', ') : 'No active events';
    }
  } catch (e) {
    if (status) status.textContent = 'EONET data unavailable';
  }
}

// ── NWS Alerts layer ─────────────────────────────────────────────────────────

async function loadNWSAlerts() {
  const status = document.getElementById('alert-status');
  try {
    const resp = await fetch(NWS_ALERTS_URL, {
      headers: { 'User-Agent': 'H3lPeR Hazards Map' }
    });
    const data = await resp.json();
    const alerts = data.features || [];

    alerts.forEach(a => {
      const p = a.properties;
      const severity = p.severity || 'Unknown';
      const color = severity === 'Extreme' ? '#b71c1c' :
                    severity === 'Severe'  ? '#e65100' :
                    severity === 'Moderate' ? '#f57f17' : '#1565c0';
      const emoji = severity === 'Extreme' ? '🚨' :
                    severity === 'Severe'  ? '⚠️' :
                    severity === 'Moderate' ? '⚡' : 'ℹ️';

      // If alert has polygon geometry, draw it
      if (a.geometry && a.geometry.coordinates) {
        const coords = a.geometry.coordinates[0].map(c => [c[1], c[0]]);
        L.polygon(coords, {
          color: color, fillColor: color, fillOpacity: 0.15, weight: 2,
        }).addTo(hazardMap).bindPopup(
          `<strong>${emoji} ${p.event}</strong><br>` +
          `${p.headline || ''}<br>` +
          `<small>Severity: ${severity}</small>`
        );
      }
    });

    if (status) {
      status.textContent = alerts.length
        ? `${alerts.length} active alert${alerts.length > 1 ? 's' : ''}`
        : 'No active alerts';
    }
  } catch (e) {
    if (status) status.textContent = 'Alert data unavailable';
  }
}

// ── Bootstrap ────────────────────────────────────────────────────────────────

async function loadHazards() {
  initMap();
  await Promise.all([loadEarthquakes(), loadEONET(), loadNWSAlerts()]);
}

document.addEventListener('DOMContentLoaded', loadHazards);
// Refresh every 15 minutes
setInterval(() => {
  if (hazardMap) {
    hazardMap.eachLayer(layer => {
      if (layer instanceof L.CircleMarker || layer instanceof L.Polygon) {
        // Don't remove the tile layer or home marker on first init
        if (layer.options && layer.options.fillColor !== '#2196f3') {
          hazardMap.removeLayer(layer);
        }
      }
    });
  }
  loadHazards();
}, 15 * 60 * 1000);
