/**
 * Natural Hazards Map — interactive Leaflet map showing live hazard data
 *
 * Data sources (all free, no API keys):
 *   - USGS Earthquake Feed: M2.5+ earthquakes from the last 7 days
 *   - NASA EONET v3: Active natural events (wildfires, storms, volcanoes, etc.)
 *   - NWS Active Alerts: Weather warnings/watches near configured location
 *   - NWS Tsunami Alerts: Active tsunami warnings/watches/advisories
 *   - USGS Flood Gauges: Sites at or above flood stage
 *   - OpenAQ: Air quality (PM2.5) station readings
 *   - RainViewer: Precipitation radar composite
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
const OPENAQ_URL = `https://api.openaq.org/v2/latest?limit=500&parameter=pm25&radius=500000&coordinates=${HAZARDS_NWS_LAT},${HAZARDS_NWS_LON}`;
const RAINVIEWER_API_URL = 'https://api.rainviewer.com/public/weather-maps.json';

let hazardMap = null;
let quakeLayer = null;
let eonetLayer = null;
let alertLayer = null;
let tsunamiLayer = null;
let floodGaugeLayer = null;
let aqiLayer = null;
let radarLayer = null;

// EONET category → display config
const EONET_CATEGORIES = {
  wildfires:    { emoji: '🔥', color: '#ff8c00', label: 'Wildfire' },
  severeStorms: { emoji: '🌀', color: '#8e44ad', label: 'Severe Storm' },
  volcanoes:    { emoji: '🌋', color: '#d35400', label: 'Volcano' },
  seaLakeIce:   { emoji: '🧊', color: '#3498db', label: 'Sea/Lake Ice' },
  floods:       { emoji: '🌊', color: '#2980b9', label: 'Flood' },
  landslides:   { emoji: '⛰️', color: '#795548', label: 'Landslide' },
  snow:         { emoji: '❄️', color: '#90caf9', label: 'Snow' },
  dustHaze:     { emoji: '🌫️', color: '#bcaaa4', label: 'Dust/Haze' },
  earthquakes:  { emoji: '〰️', color: '#a9a9a9', label: 'Earthquake' },
};

function getEonetConfig(categoryId) {
  return EONET_CATEGORIES[categoryId] || { emoji: '⚠️', color: '#f39c12', label: categoryId };
}

function quakeColor() {
  return '#a9a9a9';
}

function quakeRadius(mag) {
  return Math.max(4, Math.min(mag * 3, 24));
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
  aqiLayer = L.layerGroup().addTo(hazardMap);
  radarLayer = L.layerGroup().addTo(hazardMap);

  // Layer control for toggling overlays
  L.control.layers(null, {
    '🔴 Earthquakes': quakeLayer,
    '🌍 Natural Events': eonetLayer,
    '⚠️ Weather Alerts': alertLayer,
    '🌊 Tsunami Warnings': tsunamiLayer,
    '🌊 Flood Gauges': floodGaugeLayer,
    '🫁 Air Quality (PM2.5)': aqiLayer,
    '🌧️ Precipitation Radar': radarLayer,
  }, { collapsed: true }).addTo(hazardMap);

  // Map layer ↔ status card so toggling dims the card
  var layerCardMap = [
    [quakeLayer, 'quake-status'],
    [eonetLayer, 'eonet-status'],
    [alertLayer, 'alert-status'],
    [tsunamiLayer, 'tsunami-status'],
    [floodGaugeLayer, 'flood-gauge-status'],
    [aqiLayer, 'aqi-status'],
    [radarLayer, 'radar-status'],
  ];

  function toggleCard(layer, on) {
    var pair = layerCardMap.find(function(p) { return p[0] === layer; });
    if (!pair) return;
    var card = document.getElementById(pair[1]);
    if (card) {
      var article = card.closest('article');
      if (article) article.classList.toggle('layer-off', !on);
    }
  }

  hazardMap.on('overlayadd', function(e) { toggleCard(e.layer, true); });
  hazardMap.on('overlayremove', function(e) { toggleCard(e.layer, false); });

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
        `<strong>〰️ M${mag.toFixed(1)} Earthquake</strong><br>` +
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
      }).addTo(eonetLayer).bindPopup(
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

    sites.forEach(site => {
      const lat = parseFloat(site.dec_lat_va);
      const lon = parseFloat(site.dec_long_va);
      if (isNaN(lat) || isNaN(lon)) return;

      const cls = (site.flood_stage_class || 'action').toLowerCase();
      const style = floodGaugeStyle(cls);

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
      status.textContent = sites.length
        ? `${sites.length} site${sites.length > 1 ? 's' : ''} above flood stage`
        : 'No sites above flood stage';
    }
  } catch (e) {
    if (status) status.textContent = 'Flood gauge data unavailable';
  }
}

// ── OpenAQ Air Quality (PM2.5) layer ─────────────────────────────────────────

function aqiFromPM25(pm25) {
  // EPA AQI breakpoints for PM2.5 (µg/m³)
  const bp = [
    [0,    12.0,  0,   50],
    [12.1, 35.4,  51,  100],
    [35.5, 55.4,  101, 150],
    [55.5, 150.4, 151, 200],
    [150.5,250.4, 201, 300],
    [250.5,500.4, 301, 500],
  ];
  for (const [cLo, cHi, iLo, iHi] of bp) {
    if (pm25 >= cLo && pm25 <= cHi) {
      return Math.round(((iHi - iLo) / (cHi - cLo)) * (pm25 - cLo) + iLo);
    }
  }
  return pm25 > 500.4 ? 500 : 0;
}

function aqiColor(aqi) {
  if (aqi <= 50)  return '#4caf50'; // Good — green
  if (aqi <= 100) return '#ffeb3b'; // Moderate — yellow
  if (aqi <= 150) return '#ff9800'; // Unhealthy for Sensitive Groups — orange
  if (aqi <= 200) return '#f44336'; // Unhealthy — red
  if (aqi <= 300) return '#9c27b0'; // Very Unhealthy — purple
  return '#7e0023';                 // Hazardous — maroon
}

function aqiLabel(aqi) {
  if (aqi <= 50)  return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
  if (aqi <= 200) return 'Unhealthy';
  if (aqi <= 300) return 'Very Unhealthy';
  return 'Hazardous';
}

async function loadAQI() {
  const status = document.getElementById('aqi-status');
  try {
    const resp = await fetch(OPENAQ_URL);
    const data = await resp.json();
    const results = data.results || [];

    let stationCount = 0;
    results.forEach(loc => {
      const lat = loc.coordinates && loc.coordinates.latitude;
      const lon = loc.coordinates && loc.coordinates.longitude;
      if (lat === null || lat === undefined || lon === null || lon === undefined) return;

      const pm25Meas = (loc.measurements || []).find(m => m.parameter === 'pm25');
      if (!pm25Meas) return;

      const pm25 = pm25Meas.value;
      const aqi = aqiFromPM25(pm25);
      const color = aqiColor(aqi);
      stationCount++;

      L.circleMarker([lat, lon], {
        radius: 6,
        color: color,
        fillColor: color,
        fillOpacity: 0.8,
        weight: 1,
      }).addTo(aqiLayer).bindPopup(
        `<strong>🫁 Air Quality</strong><br>` +
        `${loc.location || 'Unknown station'}<br>` +
        `PM2.5: ${pm25.toFixed(1)} µg/m³<br>` +
        `AQI: ${aqi} — ${aqiLabel(aqi)}<br>` +
        `<small>${loc.city || ''}</small>`
      );
    });

    if (status) {
      status.textContent = stationCount
        ? `${stationCount} station${stationCount > 1 ? 's' : ''} reporting`
        : 'No AQI data available';
    }
  } catch (e) {
    if (status) status.textContent = 'AQI data unavailable';
  }
}

// ── RainViewer Precipitation Radar layer ─────────────────────────────────────

async function loadRadar() {
  const status = document.getElementById('radar-status');
  try {
    const resp = await fetch(RAINVIEWER_API_URL);
    const data = await resp.json();
    const radar = data.radar;
    if (!radar || !radar.past || !radar.past.length) {
      if (status) status.textContent = 'No radar data available';
      return;
    }

    // Use the most recent radar frame
    const latest = radar.past[radar.past.length - 1];
    const ts = latest.path; // e.g. "/v2/radar/1234567890"

    L.tileLayer(`https://tilecache.rainviewer.com${ts}/256/{z}/{x}/{y}/6/1_1.png`, {
      opacity: 0.5,
      attribution: '<a href="https://www.rainviewer.com" target="_blank">RainViewer</a>',
    }).addTo(radarLayer);

    const time = new Date(latest.time * 1000).toLocaleTimeString();
    if (status) status.textContent = `Radar composite as of ${time}`;
  } catch (e) {
    if (status) status.textContent = 'Radar data unavailable';
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
  if (aqiLayer) aqiLayer.clearLayers();
  if (radarLayer) radarLayer.clearLayers();

  await Promise.all([
    loadEarthquakes(),
    loadEONET(),
    loadNWSAlerts(),
    loadTsunamiAlerts(),
    loadFloodGauges(),
    loadAQI(),
    loadRadar(),
  ]);
}

document.addEventListener('DOMContentLoaded', loadHazards);
// Refresh every 15 minutes
setInterval(loadHazards, 15 * 60 * 1000);
