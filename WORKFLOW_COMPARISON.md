# Daily Workflow Comparison

This document explains the differences between `daily_workflow.py` and `daily_workflow_agent.py`, and documents the feature parity achieved.

## Overview

H3lPeR has two daily workflow implementations:

1. **`daily_workflow.py`** - Stable, constrained-LLM approach (RECOMMENDED)
2. **`daily_workflow_agent.py`** - Experimental, agent-centric approach

## Key Architectural Differences

### daily_workflow.py (Stable)
- **Hard-coded sections**: Weather, Space Weather, Astronomy, News, Tech News, Stocks, Research
- **Minimal LLM use**: Only for research article filtering/summarization
- **Predictable output**: Same structure every time
- **Lower hallucination risk**: LLM only operates on real data with explicit prompts
- **Direct rendering**: Uses existing article text when possible

### daily_workflow_agent.py (Experimental)
- **Autonomous agent**: Uses `AgentBriefing` class with full decision-making autonomy
- **Dynamic structure**: Agent decides what to include and how to present it
- **Higher LLM reliance**: Agent makes all content and structure decisions
- **Hallucination risk**: Agent may confabulate articles or facts (known issue)
- **JSON-based**: Outputs structured JSON that's rendered to HTML

## Feature Comparison

| Feature | daily_workflow.py | daily_workflow_agent.py |
|---------|-------------------|-------------------------|
| Weather Forecast | ✅ Hard-coded section | ✅ Agent decides |
| Space Weather | ✅ Hard-coded section | ✅ Agent decides |
| Astronomy/Sky | ✅ Hard-coded section | ✅ Agent decides |
| News Intelligence | ✅ Clustering + ranking | ✅ Agent analyzes |
| Tech News | ✅ Ranking | ✅ Agent decides |
| Stock Market | ✅ Optional section | ✅ Optional (prefs) |
| Research Papers | ✅ Filtered via LLM | ✅ Agent decides |
| Email Delivery | ✅ Markdown email | ✅ JSON-rendered email |
| **Citation Analysis** | ✅ **ADDED** | ✅ Built-in |
| **Static Site Publish** | ✅ **ADDED** | ✅ Built-in |
| Briefing Archive | ❌ Not supported | ✅ JSON archive |
| Preferences Support | ❌ Hard-coded | ✅ preferences.yaml |
| Caching | ❌ Regenerates daily | ✅ Caches by pref hash |

## Recent Updates (2026-02-15)

The stable workflow (`daily_workflow.py`) has been enhanced with two features from the agent version:

### 1. Citation Analysis
- Analyzes research papers for citation counts
- Saves results to `briefings/citations_latest.json`
- Used by static site to display trending papers
- Runs automatically after email is sent
- **Parameters**: `days=1, top_n=50, min_citations=1`

### 2. Static Site Publishing
- Generates static website from briefing content
- Publishes to GitHub Pages (tumble-dry-low.github.io)
- **Opt-in**: Requires `PAGES_DIR` or `GITHUB_PAGES_DIR` environment variable
- Includes citation page, hazards map, and briefing archives
- Auto-commits and pushes to Pages repository

## Migration Guide: Agent → Stable

If you're experiencing issues with the agent workflow (e.g., confabulated articles), migrate to the stable workflow:

### Step 1: Switch the Workflow Script

**Option A: Update GitHub Actions workflow**
```yaml
# .github/workflows/daily-briefing.yml
- name: Run Daily Briefing
  run: python daily_workflow.py  # Changed from daily_workflow_agent.py
```

**Option B: Update cron job**
```bash
# In your crontab or run_cronjob.sh
python daily_workflow.py  # Changed from daily_workflow_agent.py
```

### Step 2: Configure Environment Variables

The stable workflow now supports the same publishing features:

```bash
# Required for email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com

# Optional for static site publishing
PAGES_DIR=/path/to/tumble-dry-low.github.io
# or
GITHUB_PAGES_DIR=/path/to/tumble-dry-low.github.io

# Optional for Azure OpenAI (research filtering)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Step 3: Remove Agent-Specific Features (Optional)

The stable workflow does NOT use:
- `preferences.yaml` (except preferences read by publish_site)
- JSON briefing archives (uses markdown)
- Caching mechanism
- Agent-based content decisions

If you were relying on `preferences.yaml` for email settings, you'll need to configure those via environment variables instead.

## Known Issues

### Agent Workflow Issues
- **Confabulated research articles**: Agent may invent fake articles with plausible-sounding titles
- **Inconsistent output**: Structure varies day-to-day based on agent decisions
- **Higher token costs**: Agent makes many LLM calls for decisions

### Stable Workflow Issues
- **No preferences support**: Must use environment variables
- **No caching**: Regenerates content daily (minor performance impact)
- **Fixed structure**: Cannot adapt presentation based on importance

## Recommendation

**Use `daily_workflow.py` (stable) unless:**
- You need dynamic content structure
- You're willing to tolerate occasional hallucinations
- You want briefing archives in JSON format
- You prefer preferences.yaml over environment variables

**The stable workflow now has feature parity for:**
- Citation analysis (research paper tracking)
- Static site publishing (docs and website)
- All core briefing features

## Future Work

Potential improvements to both workflows:
- [ ] Port preferences.yaml support to stable workflow
- [ ] Add JSON archive support to stable workflow
- [ ] Reduce hallucination risk in agent workflow
- [ ] Merge best features into a single unified workflow

## Files Modified

- `daily_workflow.py` - Added citation analysis and static site publishing (24 lines added)

## Related Files

- `daily_workflow_agent.py` - Agent-centric workflow (reference implementation)
- `agent_briefing.py` - Agent system used by agent workflow
- `citations_data.py` - Citation analysis module (used by both)
- `publish_site.py` - Static site generator (used by both)
- `emailer.py` - Email delivery (used by both)

---

Last Updated: 2026-02-15
