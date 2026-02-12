/**
 * Natural Hazards Map — interactive Leaflet map showing live hazard data
 *
 * Data sources (all free, no API keys):
 *   - USGS Earthquake Feed: M2.5+ earthquakes from the last 7 days
 *   - NASA EONET v3: Active natural events (wildfires, storms, volcanoes, etc.)
 *   - NWS Active Alerts: Weather warnings/watches near configured location
 *   - NWS Tsunami Alerts: Active tsunami warnings/watches/advisories
 *   - USGS Flood Gauges: Sites at or above flood stage
 *
 * Markers use SIZE to indicate intensity (not color).
 */

const HAZARDS_NWS_LAT = 40.1657;
const HAZARDS_NWS_LON = -105.1012;

const USGS_QUAKE_URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson';
const EONET_URL = 'https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100';
const NWS_ALERTS_URL = `https://api.weather.gov/alerts/active?point=${HAZARDS_NWS_LAT},${HAZARDS_NWS_LON}`;
const NWS_TSUNAMI_URL = 'https://api.weather.gov/alerts/active?event=Tsunami%20Warning,Tsunami%20Watch,Tsunami%20Advisory';
const USGS_FLOOD_GAUGE_URL = 'https://waterwatch.usgs.gov/webservices/floodstage?format=json';

let hazardMap = null;
let quakeLayer = null;
let eonetLayer = null;
let alertLayer = null;
let tsunamiLayer = null;
let floodGaugeLayer = null;

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

function quakeColor() {
  return '#757575';
}

function quakeRadius(mag) {
  return Math.max(4, Math.min(mag * 3, 24));
}

// Distance in km between two lat/lon points (Haversine)
const LOCAL_RADIUS_KM = 500;
function distanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
function isLocal(lat, lon) {
  return distanceKm(HAZARDS_NWS_LAT, HAZARDS_NWS_LON, lat, lon) <= LOCAL_RADIUS_KM;
}

function initMap() {
  const container = document.getElementById('hazard-map');
  if (!container || hazardMap) return;

  hazardMap = L.map('hazard-map', { tap: true }).setView([HAZARDS_NWS_LAT, HAZARDS_NWS_LON], 4);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(hazardMap);

  // Home marker (persistent, not in a clearable layer group)
  L.circleMarker([HAZARDS_NWS_LAT, HAZARDS_NWS_LON], {
    radius: 6, color: '#2196f3', fillColor: '#2196f3', fillOpacity: 0.8, weight: 2,
  }).addTo(hazardMap).bindPopup('<strong>📍 Home Location</strong>');

  // Layer groups for each data source (cleared on refresh)
  quakeLayer = L.layerGroup().addTo(hazardMap);
  eonetLayer = L.layerGroup().addTo(hazardMap);
  alertLayer = L.layerGroup().addTo(hazardMap);
  tsunamiLayer = L.layerGroup().addTo(hazardMap);
  floodGaugeLayer = L.layerGroup().addTo(hazardMap);

  // Force Leaflet to recalculate container size (fixes blank map on mobile)
  setTimeout(function() { hazardMap.invalidateSize(); }, 100);
  window.addEventListener('resize', function() { hazardMap.invalidateSize(); });
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
        color: quakeColor(),
        fillColor: quakeColor(),
        fillOpacity: 0.6,
        weight: 1,
      }).addTo(quakeLayer).bindPopup(
        `<strong>🔴 M${mag.toFixed(1)} Earthquake</strong><br>` +
        `${place}<br>` +
        `Depth: ${depth.toFixed(1)} km<br>` +
        `<small>${time}</small>`
      );
    });

    const localCount = features.filter(f => {
      const [lon, lat] = f.geometry.coordinates;
      return isLocal(lat, lon);
    }).length;
    if (status) status.textContent = localCount
      ? `${localCount} nearby (${features.length} total worldwide)`
      : `None nearby (${features.length} worldwide)`;
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
    let localCounts = {};
    events.forEach(ev => {
      const catId = (ev.categories && ev.categories[0]) ? ev.categories[0].id : 'unknown';
      const cfg = getEonetConfig(catId);
      counts[cfg.label] = (counts[cfg.label] || 0) + 1;

      // Use the most recent geometry
      const geom = ev.geometry && ev.geometry[ev.geometry.length - 1];
      if (!geom || !geom.coordinates) return;

      const [lon, lat] = geom.coordinates;
      const date = geom.date ? new Date(geom.date).toLocaleDateString() : '';

      if (isLocal(lat, lon)) {
        localCounts[cfg.label] = (localCounts[cfg.label] || 0) + 1;
      }

      L.circleMarker([lat, lon], {
        radius: 7,
        color: cfg.color,
        fillColor: cfg.color,
        fillOpacity: 0.7,
        weight: 1,
      }).addTo(eonetLayer).bindPopup(
        `<strong>${cfg.emoji} ${cfg.label}</strong><br>` +
        `${ev.title}<br>` +
        (date ? `<small>${date}</small>` : '')
      );
    });

    if (status) {
      const localParts = Object.entries(localCounts).map(([k, v]) => `${v} ${k.toLowerCase()}`);
      const total = Object.values(counts).reduce((a, b) => a + b, 0);
      status.textContent = localParts.length
        ? `${localParts.join(', ')} nearby (${total} worldwide)`
        : `None nearby (${total} worldwide)`;
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
    const alertColor = '#e65100';

    alerts.forEach(a => {
      const p = a.properties;
      const severity = p.severity || 'Unknown';
      const emoji = severity === 'Extreme' ? '🚨' :
                    severity === 'Severe'  ? '⚠️' :
                    severity === 'Moderate' ? '⚡' :
                    severity === 'Minor'   ? 'ℹ️' : 'ℹ️';

      // Draw alert geometry (handles both Polygon and MultiPolygon)
      if (a.geometry && a.geometry.coordinates) {
        const popupContent =
          `<strong>${emoji} ${p.event}</strong><br>` +
          `${p.headline || ''}<br>` +
          `<small>Severity: ${severity}</small>`;
        const weight = severity === 'Extreme' ? 3 : 2;
        const style = { color: alertColor, fillColor: alertColor, fillOpacity: 0.15, weight: weight };

        if (a.geometry.type === 'MultiPolygon') {
          a.geometry.coordinates.forEach(poly => {
            const coords = poly[0].map(c => [c[1], c[0]]);
            L.polygon(coords, style).addTo(alertLayer).bindPopup(popupContent);
          });
        } else {
          const coords = a.geometry.coordinates[0].map(c => [c[1], c[0]]);
          L.polygon(coords, style).addTo(alertLayer).bindPopup(popupContent);
        }
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

// ── NOAA Tsunami Warnings layer ──────────────────────────────────────────────

async function loadTsunamiAlerts() {
  const status = document.getElementById('tsunami-status');
  try {
    const resp = await fetch(NWS_TSUNAMI_URL, {
      headers: { 'User-Agent': 'H3lPeR Hazards Map' }
    });
    const data = await resp.json();
    const alerts = data.features || [];
    const tsunamiColor = '#00bcd4';

    alerts.forEach(a => {
      const p = a.properties;
      const popupContent =
        `<strong>🌊 ${p.event}</strong><br>` +
        `${p.headline || ''}<br>` +
        `<small>Severity: ${p.severity || 'Unknown'}</small>`;
      const style = { color: tsunamiColor, fillColor: tsunamiColor, fillOpacity: 0.2, weight: 2 };

      if (a.geometry && a.geometry.coordinates) {
        if (a.geometry.type === 'MultiPolygon') {
          a.geometry.coordinates.forEach(poly => {
            const coords = poly[0].map(c => [c[1], c[0]]);
            L.polygon(coords, style).addTo(tsunamiLayer).bindPopup(popupContent);
          });
        } else if (a.geometry.type === 'Polygon') {
          const coords = a.geometry.coordinates[0].map(c => [c[1], c[0]]);
          L.polygon(coords, style).addTo(tsunamiLayer).bindPopup(popupContent);
        }
      }
    });

    if (status) {
      status.textContent = alerts.length
        ? `${alerts.length} tsunami alert${alerts.length > 1 ? 's' : ''}`
        : 'No active tsunami alerts';
    }
  } catch (e) {
    if (status) status.textContent = 'Tsunami data unavailable';
  }
}

// ── USGS Flood Gauges layer ──────────────────────────────────────────────────

function floodGaugeStyle(floodClass) {
  const styles = {
    action:   { color: '#ffc107', radius: 5 },
    flood:    { color: '#ff9800', radius: 7 },
    moderate: { color: '#e65100', radius: 9 },
    major:    { color: '#b71c1c', radius: 12 },
  };
  return styles[floodClass] || styles.action;
}

async function loadFloodGauges() {
  const status = document.getElementById('flood-gauge-status');
  try {
    const resp = await fetch(USGS_FLOOD_GAUGE_URL);
    const data = await resp.json();
    const sites = data.sites || [];

    let localCount = 0;
    sites.forEach(site => {
      const lat = parseFloat(site.dec_lat_va);
      const lon = parseFloat(site.dec_long_va);
      if (isNaN(lat) || isNaN(lon)) return;

      const cls = (site.flood_stage_class || 'action').toLowerCase();
      const style = floodGaugeStyle(cls);

      if (isLocal(lat, lon)) localCount++;

      L.circleMarker([lat, lon], {
        radius: style.radius,
        color: style.color,
        fillColor: style.color,
        fillOpacity: 0.6,
        weight: 1,
      }).addTo(floodGaugeLayer).bindPopup(
        `<strong>🌊 Flood Gauge</strong><br>` +
        `${site.station_nm || 'Unknown station'}<br>` +
        `<small>Stage: ${cls}</small>`
      );
    });

    if (status) {
      status.textContent = localCount
        ? `${localCount} nearby (${sites.length} total nationwide)`
        : `None nearby (${sites.length} nationwide)`;
    }
  } catch (e) {
    if (status) status.textContent = 'Flood gauge data unavailable';
  }
}

// ── Bootstrap ────────────────────────────────────────────────────────────────

async function loadHazards() {
  const container = document.getElementById('hazard-map');
  if (!container) return;

  try {
    initMap();
  } catch (e) {
    container.innerHTML = `<p class="error">Map failed to initialize: ${e.message}</p>`;
    return;
  }

  // Clear previous data layers before refreshing
  if (quakeLayer) quakeLayer.clearLayers();
  if (eonetLayer) eonetLayer.clearLayers();
  if (alertLayer) alertLayer.clearLayers();
  if (tsunamiLayer) tsunamiLayer.clearLayers();
  if (floodGaugeLayer) floodGaugeLayer.clearLayers();

  await Promise.all([
    loadEarthquakes(),
    loadEONET(),
    loadNWSAlerts(),
    loadTsunamiAlerts(),
    loadFloodGauges(),
  ]);
}

document.addEventListener('DOMContentLoaded', loadHazards);
// Refresh every 15 minutes
setInterval(loadHazards, 15 * 60 * 1000);
