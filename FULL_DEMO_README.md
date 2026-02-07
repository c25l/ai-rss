# Full Working Demo - Agent-Centric Briefing

This demonstrates the **complete, working agent-centric briefing system** with all enhancements.

## What This Does

1. **Fetches content** from 14 sources (news, tech, research)
2. **Calls API tools** for weather, space weather, and astronomy
3. **Agent curates** content using multi-step reasoning
4. **Generates briefing** with direct quotes and inline citations
5. **Saves output** (and can email it)

## Quick Start

### Run the Full Demo

```bash
python full_working_demo.py
```

This will:
- Show all 14 configured sources
- Test each API tool
- Fetch content from all sources
- Generate a complete briefing
- Save to `agent_briefing_YYYY-MM-DD.md`

### Run Production Workflow (with email)

```bash
# Requires .env file with email credentials
python daily_workflow_agent.py
```

This will:
- Do everything above
- Send the briefing via email (like the original workflow)

## Output Example

The agent generates briefings in this format:

```markdown
# Agent-Curated Daily Briefing - 2026-02-07

## Breaking Technology News

**[Microsoft Announces New AI Infrastructure](url)**
> "Direct quote from the article..."

**[Google Releases Update](url)**
> "Another direct quote..."

**Connection:** Brief 1-sentence connection between sources.

**Related sources:**
- [Article Title](url)
- [Another Article](url)

## Research Highlights

**[ArXiv: Paper Title](url)**
> "Key excerpt from the paper..."

## Weather & Space Conditions

**Weather:** High 65°F, low 42°F. Partly cloudy.
**Space Weather:** Kp index at 2 (quiet).
**Tonight's Sky:** Waxing crescent moon, Venus visible.
```

## What's Different from Demos

Previous demos were **partial** - they showed individual components but didn't generate actual briefings.

**This full demo:**
- ✓ Actually fetches real content
- ✓ Actually calls APIs
- ✓ Actually generates a complete briefing
- ✓ Shows the exact output format
- ✓ Works end-to-end

## Architecture

**14 Sources:**
- News: NYT, Atlantic, Heather Cox Richardson, MetaFilter, ACOUP, local news
- Tech: Microsoft Research, Google AI, TLDR Tech, Hacker News Daily
- Research: ArXiv, Nature

**8 API Tools:**
- `fetch_rss_feed()` - RSS parsing
- `scrape_webpage()` - Web scraping
- `get_weather_forecast()` - NWS weather API
- `get_space_weather()` - NOAA space weather
- `get_astronomy_viewing()` - Astronomical conditions
- `fetch_tldr_tech()` - TLDR newsletters
- `fetch_hacker_news_daily()` - HN digest
- `fetch_all_sources()` - Batch fetch

**Agent Role: CURATOR**
- Selects important content
- Uses direct quotes/excerpts
- Provides inline citations
- Minimal bridging text
- Does NOT write summaries or rewrite content

## Files

- `full_working_demo.py` - Complete working demonstration
- `daily_workflow_agent.py` - Production workflow with email
- `agent_briefing.py` - Core agent system (650+ lines)
- `demo_enhanced_features.py` - Component demos (archived)

## Requirements

```bash
pip install -r requirements.txt
```

For email functionality, create `.env`:
```
# Email settings for sending briefings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=recipient@example.com
EMAIL_PASSWORD=your-app-password
```

## Next Steps

1. Run `python full_working_demo.py` to see it work
2. Check `agent_briefing_YYYY-MM-DD.md` for output
3. Configure `.env` for email sending
4. Run `python daily_workflow_agent.py` for production use

## Comparison with Original

**Original (daily_workflow.py):**
- Hard-coded sections
- LLM only ranks content
- Fixed output format
- 5-10 small LLM calls

**Agent-Centric (daily_workflow_agent.py):**
- Dynamic sections based on content
- LLM curates and cites sources
- Adaptive output format
- 1 large LLM call with multi-step reasoning
- Preserves original text quality

Both workflows are production-ready. Choose based on your needs!
