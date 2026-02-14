# GitHub Services Migration Checklist

Use this checklist to track your migration progress.

## Pre-Migration Setup

- [ ] Read [GITHUB_SERVICES_OVERVIEW.md](GITHUB_SERVICES_OVERVIEW.md) to understand what's changing
- [ ] Verify you have access to your GitHub repository settings
- [ ] Verify you have Azure OpenAI or Anthropic API credentials
- [ ] Identify which optional services you use (stocks, Bluesky, email, etc.)

## Step 1: Create GitHub Personal Access Token

- [ ] Go to https://github.com/settings/tokens/new
- [ ] Select "Generate new token (classic)"
- [ ] Give it a descriptive name: "h3lper GitHub Pages deployment"
- [ ] Select scope: `repo` (Full control of private repositories)
- [ ] Click "Generate token"
- [ ] Copy the token (starts with `ghp_`) and save it securely
- [ ] **Important:** You won't be able to see this token again!

## Step 2: Add Secrets to GitHub Repository

Navigate to: `https://github.com/<your-username>/h3lper/settings/secrets/actions`

### Required Secrets (must have all 5)

- [ ] Add `AZURE_OPENAI_ENDPOINT`
  - Example: `https://your-resource.openai.azure.com/`
  - **Important:** Must end with `/`
  
- [ ] Add `AZURE_OPENAI_API_KEY`
  - From Azure Portal → Your OpenAI Resource → Keys and Endpoint
  
- [ ] Add `AZURE_OPENAI_DEPLOYMENT`
  - Name of your completion model deployment (e.g., `gpt-52`)
  - Find in Azure Portal → Your OpenAI Resource → Deployments
  
- [ ] Add `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
  - Name of your embedding model deployment (e.g., `text-embedding-3-large`)
  - Find in Azure Portal → Your OpenAI Resource → Deployments
  
- [ ] Add `PAGES_TOKEN`
  - The personal access token you created in Step 1

### Optional Secrets (based on preferences.yaml)

#### Stock Market Integration
- [ ] Add `ALPHA_VANTAGE_API_KEY` (if you use stock tracking)
  - Get free key at: https://www.alphavantage.co/support/#api-key

#### Bluesky Integration
- [ ] Add `BLUESKY_HANDLE` (if you use Bluesky feeds)
  - Your handle: `yourname.bsky.social`
- [ ] Add `BLUESKY_APP_PASSWORD` (if you use Bluesky feeds)
  - Create at: https://bsky.app/settings/app-passwords

#### Email Integration
- [ ] Add `FROM_EMAIL` (if you use email delivery)
- [ ] Add `TO_EMAIL` (if you use email delivery)
- [ ] Add `GOOGLE_APP_PW` (if you use Gmail SMTP)
  - Create at: https://myaccount.google.com/apppasswords

#### Sonarr Integration
- [ ] Add `SONARR_URL` (if you use Sonarr tracking)
- [ ] Add `SONARR_API_KEY` (if you use Sonarr tracking)

## Step 3: Verify GitHub Pages Repository

- [ ] Confirm you have a GitHub Pages repository
  - Name format: `<username>.github.io` (e.g., `tumble-dry-low.github.io`)
  - If not, create one: https://github.com/new
  
- [ ] Verify the repository name in `.github/workflows/daily-briefing.yml`
  - Look for: `repository: tumble-dry-low/tumble-dry-low.github.io`
  - Update if your username is different

- [ ] Ensure GitHub Pages is enabled in that repository
  - Go to repository Settings → Pages
  - Source should be set to "Deploy from a branch"
  - Branch should be `main` or `master`

## Step 4: Push Workflow File

In your local h3lper repository:

```bash
# Ensure you're on the right branch
git status

# Add the workflow file
git add .github/workflows/daily-briefing.yml

# Commit
git commit -m "Add GitHub Actions workflow for automated briefing"

# Push
git push origin main
```

- [ ] Workflow file pushed to GitHub
- [ ] No errors during push

## Step 5: First Test Run

- [ ] Navigate to your repository on GitHub
- [ ] Click the "Actions" tab at the top
- [ ] You should see "Daily Briefing" in the list of workflows
- [ ] Click "Daily Briefing"
- [ ] Click "Run workflow" button (on the right side)
- [ ] Select branch (usually `main`)
- [ ] Click green "Run workflow" button
- [ ] Wait for workflow to start (~10 seconds)

## Step 6: Monitor First Run

- [ ] Click on the running workflow (yellow dot)
- [ ] Watch the "generate-and-publish" job
- [ ] Expand steps to see detailed logs
- [ ] Wait for completion (~5-10 minutes)

### Expected Results
- [ ] "Generate daily briefing" step completes successfully
- [ ] Python script output appears in logs
- [ ] "Commit and push to GitHub Pages" step runs
- [ ] Green checkmark on workflow run

### If Errors Occur
- [ ] Read error message carefully
- [ ] Common issues:
  - Missing or incorrect secrets → Go back to Step 2
  - Invalid endpoint URL → Must end with `/`
  - Deployment name mismatch → Check Azure portal
  - Token expired or wrong scope → Recreate token in Step 1

## Step 7: Verify GitHub Pages Update

- [ ] Go to your GitHub Pages repository
- [ ] Check for new commit from "github-actions[bot]"
- [ ] Visit your site: `https://<username>.github.io`
- [ ] Verify today's briefing appears
- [ ] Check that all sections loaded correctly

## Step 8: Download Artifacts (Optional)

- [ ] Return to workflow run page
- [ ] Scroll to bottom to "Artifacts" section
- [ ] Download `briefing-<run-id>` ZIP file
- [ ] Extract and verify JSON file is present and valid

## Step 9: Configure Schedule

The workflow is set to run daily at 7:00 AM UTC by default.

To change the schedule:
- [ ] Edit `.github/workflows/daily-briefing.yml`
- [ ] Find the `cron:` line (line 6)
- [ ] Update time using cron syntax: `'0 7 * * *'`
  - Format: `'minute hour day month weekday'`
  - Example: `'30 14 * * *'` = 2:30 PM UTC daily
  - Use https://crontab.guru to help
- [ ] Commit and push the change

## Step 10: Set Up Notifications (Optional)

To get notified of failures:

- [ ] Go to GitHub Settings → Notifications
- [ ] Scroll to "Actions" section
- [ ] Enable notifications for workflow failures
- [ ] Choose notification method (email, web, mobile)

## Step 11: Disable Local Cron Job

**Only do this after confirming GitHub Actions works!**

- [ ] List current cron jobs: `crontab -l`
- [ ] Edit crontab: `crontab -e`
- [ ] Comment out or delete the h3lper line
- [ ] Save and exit
- [ ] Verify: `crontab -l` should not show h3lper

## Step 12: Monitor for a Week

- [ ] Check Actions tab daily for first week
- [ ] Verify briefings are generating successfully
- [ ] Monitor GitHub Pages site updates
- [ ] Check for any failure notifications

## Troubleshooting

### Workflow doesn't appear in Actions tab
→ Make sure `.github/workflows/daily-briefing.yml` is pushed to `main` branch

### Workflow fails immediately
→ Check all required secrets are set correctly in Step 2

### LLM generation fails
→ Verify Azure OpenAI credentials and deployment names

### Git push fails
→ Verify `PAGES_TOKEN` has `repo` scope and hasn't expired

### Pages don't update
→ Check GitHub Pages repository exists and Pages is enabled

### Need more help?
→ Read [GITHUB_SERVICES_MIGRATION.md](GITHUB_SERVICES_MIGRATION.md) for detailed troubleshooting

## Rollback Plan

If something goes wrong and you need to revert:

- [ ] Re-enable local cron job: `crontab -e`
- [ ] Disable GitHub Actions workflow:
  - Rename `.github/workflows/daily-briefing.yml` to `daily-briefing.yml.disabled`
  - Or delete the file entirely
  - Commit and push
- [ ] Your local setup will work as before

## Success Criteria

You've successfully migrated when:

- ✅ GitHub Actions workflow runs automatically every day
- ✅ Briefings appear on your GitHub Pages site
- ✅ No manual intervention needed
- ✅ Local cron job is disabled
- ✅ Workflow runs for a week without issues

## Next Steps After Migration

- [ ] Update `preferences.yaml` if needed
- [ ] Customize workflow schedule
- [ ] Set up failure notifications
- [ ] Archive local briefing files
- [ ] Document your specific configuration for future reference

## Notes

Use this space to track issues, customizations, or important details:

```
Date migrated: ___________

Custom settings:
- 

Issues encountered:
- 

Solutions applied:
- 

```

---

**Need help?** Open an issue on GitHub with:
- What step you're on
- Error message (if any)
- Screenshot of workflow run (if applicable)
