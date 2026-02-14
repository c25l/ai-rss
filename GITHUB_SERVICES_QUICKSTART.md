# GitHub Services Quick Start

This is a condensed guide for migrating h3lper to GitHub Actions. For detailed information, see [GITHUB_SERVICES_MIGRATION.md](GITHUB_SERVICES_MIGRATION.md).

## Prerequisites

- GitHub repository with h3lper code
- GitHub Pages repository (e.g., `username.github.io`)
- Azure OpenAI account OR Anthropic API key

## 5-Minute Setup

### 1. Create GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Check the `repo` scope
4. Copy the token (starts with `ghp_`)

### 2. Add GitHub Secrets
Go to your repository **Settings > Secrets and variables > Actions** and add:

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-52
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
GITHUB_PAGES_TOKEN=ghp_your_token_here
```

### 3. Push Workflow File
```bash
git add .github/workflows/daily-briefing.yml
git commit -m "Add GitHub Actions workflow"
git push
```

### 4. Test Run
1. Go to **Actions** tab in your repository
2. Click "Daily Briefing" workflow
3. Click "Run workflow" button
4. Wait ~5 minutes
5. Check your GitHub Pages site

### 5. Done!
The workflow will now run automatically every day at 7:00 AM UTC.

## Optional: Add More Secrets

Based on your `preferences.yaml`, you may want to add:

- `ALPHA_VANTAGE_API_KEY` - For stock data
- `BLUESKY_HANDLE` / `BLUESKY_APP_PASSWORD` - For social media
- `FROM_EMAIL` / `TO_EMAIL` / `GOOGLE_APP_PW` - For email notifications

## Troubleshooting

### Workflow fails immediately
- Check that all required secrets are set
- Verify `GITHUB_PAGES_TOKEN` has `repo` scope

### Workflow runs but pages don't update
- Check the GitHub Pages repository exists
- Verify the token has write access to that repository
- Look at workflow logs for git push errors

### LLM generation fails
- Verify Azure OpenAI credentials are correct
- Check endpoint URL format: must end with `/`
- Ensure deployment names match your Azure setup

## What Gets Automated

✅ Daily briefing generation  
✅ GitHub Pages deployment  
✅ Briefing JSON archival (90 days)  
✅ Python dependency management  
✅ Error notifications (via GitHub email)  

## What You Still Need

🔑 Azure OpenAI or Anthropic API (for LLM)  
🔑 Alpha Vantage API (optional, for stocks)  
🔑 Bluesky credentials (optional, for social media)  
📧 SMTP credentials (optional, for email)  

## Cost

**Free** - GitHub Actions provides 2,000 minutes/month for private repos, unlimited for public repos. This workflow uses ~5-10 minutes per day (~150-300 minutes/month).

## Next Steps

- Disable your local cron job: `crontab -e`
- Monitor the first few runs in the Actions tab
- Customize the schedule in `.github/workflows/daily-briefing.yml`
- Read [GITHUB_SERVICES_MIGRATION.md](GITHUB_SERVICES_MIGRATION.md) for advanced configuration

## Support

Issues? Check the workflow logs in the Actions tab for detailed error messages.
