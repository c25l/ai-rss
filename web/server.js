const express = require('express');
const path = require('path');
const fs = require('fs');
const { pythonCall } = require('./lib/python-bridge');

const app = express();
const PORT = process.env.PORT || 3000;

// The H3lPeR project root (one level up from web/)
const PROJECT_ROOT = path.resolve(__dirname, '..');
const BRIEFINGS_DIR = path.join(PROJECT_ROOT, 'briefings');
const PREFERENCES_FILE = path.join(PROJECT_ROOT, 'preferences.yaml');

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ============================================================================
// HELPERS
// ============================================================================

function loadPreferences() {
  try {
    const yaml = require('js-yaml');
    const raw = fs.readFileSync(PREFERENCES_FILE, 'utf8');
    return yaml.load(raw) || {};
  } catch (e) {
    return {};
  }
}

// ============================================================================
// ROUTES
// ============================================================================

// Dashboard — pass stock symbols from preferences
app.get('/', (req, res) => {
  const prefs = loadPreferences();
  const stockSymbols = prefs.stock_symbols || ['MSFT', 'NVDA', 'FOREXCOM:DJI', 'FOREXCOM:SPX500'];
  res.render('dashboard', { page: 'dashboard', stockSymbols });
});

// Briefings list
app.get('/briefings', async (req, res) => {
  const fs = require('fs');
  let briefings = [];

  try {
    const files = fs.readdirSync(BRIEFINGS_DIR)
      .filter(f => f.endsWith('.json'))
      .sort()
      .reverse();

    for (const file of files) {
      try {
        const raw = fs.readFileSync(path.join(BRIEFINGS_DIR, file), 'utf8');
        const doc = JSON.parse(raw);
        // Extract date from filename (YYMMDD-hash.json)
        const match = file.match(/^(\d{6})-/);
        let dateStr = file;
        if (match) {
          const yy = match[1].slice(0, 2);
          const mm = match[1].slice(2, 4);
          const dd = match[1].slice(4, 6);
          dateStr = `20${yy}-${mm}-${dd}`;
        }
        briefings.push({
          filename: file,
          date: dateStr,
          title: doc.title || 'Untitled Briefing',
          sectionCount: (doc.children || []).length
        });
      } catch (e) {
        // Skip malformed files
      }
    }
  } catch (e) {
    // briefings dir may not exist yet
  }

  // If HTMX request, return just the content fragment
  if (req.headers['hx-request']) {
    return res.render('partials/briefing-list', { briefings });
  }
  res.render('briefings', { page: 'briefings', briefings });
});

// Single briefing view — render JSON → HTML via Python
app.get('/briefings/:filename', async (req, res) => {
  const fs = require('fs');
  const filePath = path.join(BRIEFINGS_DIR, req.params.filename);

  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    const doc = JSON.parse(raw);

    // Render HTML using the Python emailer's render function
    const html = await pythonCall('render_briefing', JSON.stringify(doc));

    if (req.headers['hx-request']) {
      return res.send(html);
    }
    res.render('briefing', { page: 'briefings', briefingHtml: html, filename: req.params.filename });
  } catch (e) {
    const errMsg = `<p>Error loading briefing: ${e.message}</p>`;
    if (req.headers['hx-request']) return res.send(errMsg);
    res.render('briefing', { page: 'briefings', briefingHtml: errMsg, filename: req.params.filename });
  }
});

// Settings page
app.get('/settings', (req, res) => {
  res.render('settings', { page: 'settings' });
});

// ============================================================================
// API
// ============================================================================

// Serve preferences (for client-side widgets that need config)
app.get('/api/preferences', (req, res) => {
  const prefs = loadPreferences();
  res.json(prefs);
});

// ============================================================================
// START
// ============================================================================

const HOST = process.env.HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`H3lPeR web app running at http://${HOST}:${PORT}`);
  console.log(`Project root: ${PROJECT_ROOT}`);
});
