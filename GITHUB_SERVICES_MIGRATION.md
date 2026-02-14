# GitHub Services Migration Guide

This guide explains how to migrate the h3lper project to run entirely on GitHub services, making it self-contained and eliminating the need for external infrastructure.

## Overview

The h3lper project can be fully automated using GitHub's built-in services:

1. **GitHub Actions** - Replaces cron jobs for scheduled execution
2. **GitHub Secrets** - Secure storage for API keys and credentials
3. **GitHub Pages** - Static site hosting (already in use)
4. **GitHub Artifacts** - Briefing JSON archive storage

## Current Architecture vs. GitHub Services

### Before (Local/Cron-based)
```
┌─────────────────┐
│  Local Machine  │
│                 │
│  ┌───────────┐  │
│  │ Cron Job  │  │ ← Runs daily_workflow_agent.py
│  └─────┬─────┘  │
│        │        │
│        v        │
│  ┌───────────┐  │
│  │ H3lPeR    │  │ ← Generates briefing
│  │ Python    │  │
│  └─────┬─────┘  │
│        │        │
│        v        │
│  ┌───────────┐  │
│  │ Git Push  │  │ ← Pushes to GitHub Pages repo
│  └───────────┘  │
└─────────────────┘
```

### After (GitHub Services)
```
┌─────────────────────────────────────────┐
│         GitHub Infrastructure           │
│                                         │
│  ┌──────────────────┐                  │
│  │  GitHub Actions  │                  │
│  │  (Scheduled)     │ ← Runs daily    │
│  └────────┬─────────┘                  │
│           │                            │
│           v                            │
│  ┌──────────────────┐                  │
│  │  Ubuntu Runner   │                  │
│  │  - Python        │                  │
│  │  - H3lPeR code   │                  │
│  └────────┬─────────┘                  │
│           │                            │
│           v                            │
│  ┌──────────────────┐                  │
│  │  GitHub Pages    │ ← Auto-deploy   │
│  │  Static Site     │                  │
│  └──────────────────┘                  │
│                                         │
│  ┌──────────────────┐                  │
│  │  GitHub Secrets  │ ← API keys       │
│  └──────────────────┘                  │
│                                         │
│  ┌──────────────────┐                  │
│  │  Artifacts       │ ← Briefing JSONs │
│  └──────────────────┘                  │
└─────────────────────────────────────────┘
```

## Migration Steps

### 1. Set Up GitHub Secrets

Navigate to your repository's **Settings > Secrets and variables > Actions** and add these secrets:

#### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_DEPLOYMENT` | Completion model deployment name | `gpt-52` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name | `text-embedding-3-large` |
| `PAGES_TOKEN` | Personal Access Token with repo permissions | `ghp_...` |

#### Optional Secrets (based on your preferences.yaml)

| Secret Name | Description |
|-------------|-------------|
| `ANTHROPIC_API_KEY` | Fallback LLM if Azure unavailable |
| `BLUESKY_HANDLE` | For social media integration |
| `BLUESKY_APP_PASSWORD` | Bluesky app password |
| `ALPHA_VANTAGE_API_KEY` | Stock market data |
| `FROM_EMAIL` | Email sender address |
| `TO_EMAIL` | Email recipient address |
| `GOOGLE_APP_PW` | Gmail app password for SMTP |
| `SONARR_URL` | Media server integration |
| `SONARR_API_KEY` | Sonarr API key |

### 2. Create GitHub Personal Access Token (PAT)

The workflow needs a PAT to push to your GitHub Pages repository:

1. Go to **Settings > Developer settings > Personal access tokens > Tokens (classic)**
2. Click **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
4. Generate and copy the token
5. Add it as `PAGES_TOKEN` secret

### 3. Enable GitHub Actions

The workflow file `.github/workflows/daily-briefing.yml` has been created. To activate it:

1. Commit and push the `.github/workflows/` directory
2. Go to **Actions** tab in your repository
3. You should see "Daily Briefing" workflow
4. It will run automatically at 7:00 AM UTC daily
5. You can also trigger it manually via "Run workflow" button

### 4. Configure GitHub Pages Repository

If you don't already have a GitHub Pages repository:

1. Create a repository named `<username>.github.io` (e.g., `tumble-dry-low.github.io`)
2. Enable GitHub Pages in repository settings
3. Update the workflow file if your repo name is different:
   ```yaml
   repository: your-username/your-username.github.io
   ```

### 5. Update preferences.yaml (Optional)

You can control workflow behavior via `preferences.yaml`:

```yaml
email_preferences:
  send_email: false  # Set to true if using email via GitHub Actions
  publish_site: true # Enable static site publishing
  subject_format: "H3LPeR Briefing - {date}"
```

### 6. Test the Workflow

#### Manual Test Run
1. Go to **Actions** tab
2. Select "Daily Briefing" workflow
3. Click "Run workflow"
4. Wait for completion (~5-10 minutes)
5. Check your GitHub Pages site

#### View Logs
- Click on any workflow run to see detailed logs
- Each step shows output (including Python script execution)
- Errors will appear in red with full stack traces

#### Download Artifacts
- Briefing JSON files are archived for 90 days
- Download from workflow run page under "Artifacts"

### 7. Disable Local Cron Job

Once GitHub Actions is working:

```bash
# List current cron jobs
crontab -l

# Remove h3lper cron job
crontab -e
# Delete the line containing daily_workflow_agent.py

# Verify
crontab -l
```

## What Runs Where

### GitHub Actions Handles
- ✅ Scheduled daily execution
- ✅ Python environment setup
- ✅ Dependency installation
- ✅ Briefing generation
- ✅ GitHub Pages deployment
- ✅ Briefing archive (as artifacts)

### External Services Still Required
- 🔑 Azure OpenAI or Anthropic (LLM)
- 🔑 Alpha Vantage (stocks) - optional
- 🔑 Bluesky (social media) - optional
- 📧 SMTP server (email) - optional

### No Credentials Needed
- ✅ USGS Earthquake API (public)
- ✅ NASA EONET API (public)
- ✅ NWS Weather API (public)
- ✅ NOAA Space Weather (public)
- ✅ arXiv RSS Feeds (public)
- ✅ Semantic Scholar API (public, rate-limited)

## Monitoring and Debugging

### Check Workflow Status
```bash
# Via GitHub CLI
gh run list --workflow=daily-briefing.yml

# View latest run
gh run view --log

# Watch a running workflow
gh run watch
```

### Common Issues

#### Issue: Workflow fails with authentication error
**Solution:** Verify `PAGES_TOKEN` has `repo` scope and hasn't expired

#### Issue: Missing dependencies
**Solution:** Check `requirements.txt` is up to date. The workflow caches pip packages.

#### Issue: LLM generation timeout
**Solution:** Azure OpenAI may be slow. The default timeout is 300 seconds (5 minutes).

#### Issue: Git push fails
**Solution:** Ensure the GitHub Pages repository exists and the PAT has write access

### Email Notifications

Configure GitHub to email you on workflow failures:
1. Go to **Settings > Notifications**
2. Enable **Actions** notifications
3. Choose email frequency

Alternatively, modify the workflow to send custom notifications:
```yaml
- name: Notify on failure
  if: failure()
  run: |
    # Add custom notification logic here
    # (email, Slack, Discord, etc.)
```

## Cost Considerations

### GitHub Actions Free Tier
- ✅ 2,000 minutes/month for private repos
- ✅ Unlimited for public repos
- Each run uses ~5-10 minutes
- Daily execution = ~150-300 minutes/month
- **Well within free tier limits**

### GitHub Pages
- ✅ Free for public repositories
- ✅ 100 GB bandwidth/month
- ✅ 1 GB storage

### Artifacts Storage
- ✅ 500 MB free storage
- ✅ Briefing JSONs are small (~50-200 KB each)
- 90-day retention = ~90 files = ~5-20 MB total

## Advanced Configuration

### Change Schedule

Edit `.github/workflows/daily-briefing.yml`:
```yaml
on:
  schedule:
    # Run at 6:00 AM and 6:00 PM UTC
    - cron: '0 6,18 * * *'
```

### Multiple Workflows

Create separate workflows for different purposes:
- `daily-briefing.yml` - Main daily briefing
- `weekly-summary.yml` - Weekly digest
- `on-demand.yml` - Manual execution only

### Conditional Execution

Skip execution based on conditions:
```yaml
- name: Check if weekend
  id: check-day
  run: |
    if [ $(date +%u) -gt 5 ]; then
      echo "skip=true" >> $GITHUB_OUTPUT
    fi

- name: Generate briefing
  if: steps.check-day.outputs.skip != 'true'
  run: python daily_workflow_agent.py
```

## Rollback Plan

If GitHub Actions doesn't work for you:

1. Keep the original `run_cronjob.sh` and cron configuration
2. Both can run simultaneously (cron as backup)
3. Disable GitHub Actions workflow: rename the `.yml` file or delete it
4. The local setup will continue working as before

## Benefits of GitHub Services

✅ **No local infrastructure** - Runs on GitHub's servers  
✅ **Automatic scaling** - GitHub handles resource allocation  
✅ **Built-in monitoring** - Workflow logs and notifications  
✅ **Version controlled** - Workflow configuration in git  
✅ **Free for public repos** - No additional cost  
✅ **Reliable scheduling** - Better than personal machine uptime  
✅ **Artifact archiving** - Automatic briefing backup  
✅ **Easy debugging** - Full logs available in UI  

## Next Steps

1. ✅ Review this guide
2. ✅ Set up GitHub Secrets
3. ✅ Create GitHub PAT
4. ✅ Push workflow file to repository
5. ✅ Test manual workflow run
6. ✅ Verify GitHub Pages deployment
7. ✅ Disable local cron job
8. ✅ Monitor first few automated runs

## Support

For issues with:
- **GitHub Actions**: Check [GitHub Actions documentation](https://docs.github.com/en/actions)
- **GitHub Pages**: Check [GitHub Pages documentation](https://docs.github.com/en/pages)
- **h3lper-specific issues**: Open an issue in this repository

## Summary

By moving to GitHub services, h3lper becomes:
- 🌐 **Fully cloud-based** - No local machine required
- 🔐 **Secure** - Secrets encrypted by GitHub
- 📈 **Scalable** - Runs on GitHub infrastructure
- 💰 **Free** - Within GitHub's generous free tiers
- 🛠️ **Maintainable** - All configuration version controlled
