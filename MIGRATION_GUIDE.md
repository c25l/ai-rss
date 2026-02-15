# Migration Complete: Agent → Stable Workflow

## Quick Start

If you're experiencing issues with `daily_workflow_agent.py` confabulating research articles, switch to the stable workflow:

### 1. Update Your Run Script

**GitHub Actions** (`.github/workflows/daily-briefing.yml`):
```yaml
- name: Run Daily Briefing
  run: python daily_workflow.py
```

**Cron Job** (`run_cronjob.sh` or crontab):
```bash
python daily_workflow.py
```

### 2. Verify Environment Variables

The stable workflow now supports the same features. Ensure these are set:

```bash
# Required for email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com

# Required for Azure OpenAI (research filtering)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Optional: Enable static site publishing
PAGES_DIR=/path/to/tumble-dry-low.github.io
# or
GITHUB_PAGES_DIR=/path/to/tumble-dry-low.github.io
```

### 3. Done!

The stable workflow will now:
- ✅ Generate daily briefing with all sections
- ✅ Send email
- ✅ Run citation analysis on research papers
- ✅ Publish to static website (if PAGES_DIR is set)

**Without** the agent's confabulation issues.

## What Changed

The stable workflow (`daily_workflow.py`) now includes:

1. **Citation Analysis** - Tracks research paper citations, saves to `briefings/citations_latest.json`
2. **Static Site Publishing** - Generates and publishes website to GitHub Pages

These were the only features missing from the stable workflow that existed in the agent version.

## Why Switch?

| Aspect | Stable Workflow | Agent Workflow |
|--------|----------------|----------------|
| **Reliability** | ✅ Consistent output | ⚠️ Variable quality |
| **Accuracy** | ✅ No confabulation | ❌ Makes up articles |
| **Structure** | ✅ Predictable sections | ⚠️ Agent decides |
| **Performance** | ✅ Faster, fewer LLM calls | ⚠️ More API usage |
| **Features** | ✅ Citations + Publishing | ✅ Citations + Publishing |

## Full Documentation

See [WORKFLOW_COMPARISON.md](WORKFLOW_COMPARISON.md) for:
- Detailed architectural comparison
- Feature matrix
- Known issues
- Future improvements

---

Last Updated: 2026-02-15
