# H3lPeR - Personal Briefing System

AI-powered daily briefing system that aggregates news, research papers, weather, astronomy, and more into a personalized digest.

## Features

- 🤖 **AI-Driven Content Curation** - Uses Azure OpenAI or Anthropic Claude to rank and summarize content
- 📰 **Multi-Source Aggregation** - News, research papers (arXiv), Bluesky feeds, weather, astronomy
- 📊 **Citation Analysis** - Identifies influential papers by analyzing citation graphs
- 🗺️ **Natural Hazards Map** - Interactive map showing earthquakes, weather alerts, wildfires
- 📈 **Market Dashboard** - Stock tracking and visualization
- 📧 **Email Delivery** - Receive briefings via email
- 🌐 **Static Site** - Beautiful web interface hosted on GitHub Pages

## Quick Start

### GitHub Actions (Recommended)

Run h3lper completely on GitHub infrastructure - no local machine required!

**⚡ 5-minute setup:** [GITHUB_SERVICES_QUICKSTART.md](GITHUB_SERVICES_QUICKSTART.md)

**📚 Detailed guide:** [GITHUB_SERVICES_MIGRATION.md](GITHUB_SERVICES_MIGRATION.md)

**❓ Overview:** [GITHUB_SERVICES_OVERVIEW.md](GITHUB_SERVICES_OVERVIEW.md)

### Local Installation

```bash
# Clone repository
git clone https://github.com/tumble-dry-low/h3lper.git
cd h3lper

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run daily briefing
python daily_workflow_agent.py
```

## Configuration

### Required
- Azure OpenAI OR Anthropic API key (for LLM)

### Optional
- Alpha Vantage API key (stock data)
- Bluesky credentials (social media feeds)
- Email credentials (briefing delivery)
- Sonarr API (media tracking)

See [.env.example](.env.example) for all options.

## Project Structure

```
h3lper/
├── agent_briefing.py       # Core briefing generation
├── daily_workflow_agent.py # Daily execution orchestrator
├── publish_site.py         # Static site generator
├── copilot.py             # LLM interface (Azure/Claude)
├── research.py            # Research paper aggregation
├── arxiv_citations.py     # Citation graph analysis
├── weather.py             # Weather data
├── astronomy.py           # Astronomical events
├── stocks.py              # Stock market data
├── web/                   # Static site frontend
│   ├── public/           # HTML, CSS, JS
│   └── server.js         # Optional local server
└── .github/
    └── workflows/         # GitHub Actions automation
```

## Documentation

- [LLM Configuration](LLM_CONFIG.md) - Azure OpenAI vs Anthropic setup
- [Citation Analysis](ARXIV_CITATIONS.md) - Research paper citation tracking
- [Feature Summary](FEATURE_SUMMARY.md) - Complete feature list
- [Enhancements Guide](ENHANCEMENTS_GUIDE.md) - Contribution guidelines

### GitHub Services Migration
- [Overview](GITHUB_SERVICES_OVERVIEW.md) - What's involved in moving to GitHub
- [Quick Start](GITHUB_SERVICES_QUICKSTART.md) - 5-minute setup guide
- [Migration Guide](GITHUB_SERVICES_MIGRATION.md) - Detailed step-by-step instructions

## Usage

### Manual Execution
```bash
python daily_workflow_agent.py
```

### Scheduled Execution

**Local (cron):**
```bash
0 7 * * * cd /path/to/h3lper && python daily_workflow_agent.py
```

**GitHub Actions (recommended):**
See [GITHUB_SERVICES_QUICKSTART.md](GITHUB_SERVICES_QUICKSTART.md)

### Publish Static Site
```bash
# Generate static site
python publish_site.py

# Generate without git push
python publish_site.py --no-push
```

## Example Output

Daily briefings include:
- Top news stories (ranked by AI)
- Influential research papers (by citation count)
- Weather forecast and alerts
- Astronomical events (moon phase, planets visible)
- Market summary (if enabled)
- Natural hazards map
- Custom sections from your preferences

View a live example at: https://tumble-dry-low.github.io

## Architecture

### Data Sources (All Free/Public APIs)
- arXiv (research papers)
- USGS (earthquakes)
- NASA EONET (natural events)
- NWS (weather alerts)
- NOAA (space weather)
- Semantic Scholar (citations)

### LLM Providers (Your API Key)
- Azure OpenAI (recommended)
- Anthropic Claude (fallback)

### Deployment Options
1. **GitHub Actions** (fully automated, no infrastructure)
2. **Local cron job** (traditional approach)
3. **Manual execution** (on-demand)

## Customization

Edit `preferences.yaml` to customize:
- News categories and feeds
- Research topics (arXiv categories)
- Bluesky feeds to monitor
- Email preferences
- Stock portfolio
- Location (for weather)

## License

[Add your license here]

## Contributing

Contributions welcome! See [ENHANCEMENTS_GUIDE.md](ENHANCEMENTS_GUIDE.md) for guidelines.

## Support

For questions or issues:
1. Check the documentation in this repository
2. Review workflow logs (if using GitHub Actions)
3. Open an issue on GitHub

## Credits

Created by [your name/handle]

Uses:
- Azure OpenAI / Anthropic Claude for content ranking
- Leaflet.js for interactive maps
- Chart.js for visualizations
- Pico CSS for styling
- Various public APIs for data
