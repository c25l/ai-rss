# LLM Configuration Guide

This document explains how to configure the LLM backend for h3lper.

## Overview

h3lper supports three modes of operation for LLM calls (in priority order):

1. **Azure OpenAI** (Highest Priority): Uses your Azure OpenAI deployment
2. **Anthropic API** (Second Priority): Direct API calls to Anthropic's Claude models
3. **GitHub Copilot CLI** (Fallback): Uses the local `copilot` CLI command

The system automatically selects the best available mode based on your configuration.

## Configuration

### Option 1: Azure OpenAI (Recommended if you have Azure)

This is the highest priority mode. If all 4 required environment variables are set, this mode will be used.

1. Get your Azure OpenAI credentials from Azure Portal → Azure OpenAI Service

2. Add them to your `.env` file:
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_azure_openai_key_here
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

3. Install the openai package (if not already installed):
   ```bash
   pip install openai>=1.12.0
   ```

4. The system will use your deployment name as the model

**Note:** Your deployment can be GPT-4, Claude via Azure, or any other model you've deployed.

### Option 2: Anthropic API (Recommended if no Azure)

If Azure OpenAI is not configured, the system falls back to Anthropic's direct API.

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)

2. Add it to your `.env` file:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
   ```

3. Install the anthropic package (if not already installed):
   ```bash
   pip install anthropic>=0.18.0
   ```

4. (Optional) Set your preferred model:
   ```bash
   COPILOT_MODEL=claude-3-5-sonnet-20241022
   ```
   Default for Anthropic mode: `claude-3-5-sonnet-20241022`

### Option 3: GitHub Copilot CLI (Fallback)

If neither Azure nor Anthropic is configured, the system automatically falls back to the CLI.

1. Ensure you have the GitHub Copilot CLI installed:
   ```bash
   which copilot
   # Should show: /usr/local/bin/copilot (or similar)
   ```

2. (Optional) Set your preferred model:
   ```bash
   COPILOT_MODEL=claude-opus-4.6
   ```
   Default for CLI mode: `claude-opus-4.6`

## Automatic Mode Selection

The system automatically selects the best available mode:

```
┌─────────────────────────────────┐
│ Azure OpenAI configured?        │
│ (all 4 env vars + openai pkg)  │
└────────┬────────────────────────┘
         │
    ┌────▼────┐
    │   YES   │
    └────┬────┘
         │
    ┌────▼────┐
    │  AZURE  │
    │  MODE   │
    └─────────┘
         
         │ NO
         │
    ┌────▼─────────────────────────┐
    │ ANTHROPIC_API_KEY set?       │
    │ (anthropic package OK?)      │
    └────┬────────────────┬────────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │   YES   │      │   NO    │
    └────┬────┘      └────┬────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │ANTHROPIC│      │   CLI   │
    │  MODE   │      │  MODE   │
    └─────────┘      └─────────┘
```

## Fallback Behavior

If the selected mode fails on the first attempt, the system automatically tries fallback modes:

**Azure OpenAI → Anthropic API → CLI**

Example:
1. Azure OpenAI configured and tried first
2. Azure fails (e.g., quota exceeded, network issue)
3. System automatically tries Anthropic API (if key available)
4. If Anthropic also fails, tries CLI
5. Returns result from first successful mode

This provides maximum reliability across all scenarios.

## Troubleshooting

### Issue: Hanging during research ranking

**Symptoms:** The system prints "generating from..." and then hangs indefinitely.

**Solution:** This was caused by CLI mode not closing stdin. Fixed by adding `stdin=subprocess.DEVNULL`.

### Issue: Azure API calls failing

**Symptoms:** Errors mentioning "Azure" or "OpenAI".

**Solution:**
1. Verify all 4 Azure environment variables are set correctly
2. Check endpoint URL format: `https://your-resource.openai.azure.com/`
3. Verify API key is valid
4. Confirm deployment name matches your Azure deployment
5. Check API version is compatible (2024-02-15-preview recommended)
6. Ensure the openai package is installed: `pip install openai`

### Issue: Anthropic API calls failing

**Symptoms:** Errors mentioning "Anthropic" or "API key".

**Solution:**
1. Verify your API key is correct
2. Check you have credits/usage available in your Anthropic account
3. Ensure the anthropic package is installed: `pip install anthropic`

### Issue: CLI not found

**Symptoms:** Errors about `/usr/local/bin/copilot` not being found.

**Solution:**
1. Install GitHub Copilot CLI
2. Or set `AZURE_OPENAI_*` variables to use Azure mode
3. Or set `ANTHROPIC_API_KEY` to use Anthropic mode

## Model Selection

Different modes use different models:

| Mode | Default Model | Configurable Via | Notes |
|------|--------------|------------------|-------|
| Azure OpenAI | Deployment name | Azure Portal deployment | Can be GPT-4, Claude, etc. |
| Anthropic API | claude-3-5-sonnet-20241022 | COPILOT_MODEL env var | Fast and cost-effective |
| CLI | claude-opus-4.6 | COPILOT_MODEL env var | Depends on CLI availability |

You can override defaults by setting `COPILOT_MODEL` in your `.env`.

## Testing Your Configuration

Run this test to verify your configuration:

```bash
python3 -c "
from copilot import Copilot
c = Copilot()
print(f'Mode: {c.mode}')
print(f'Model: {c.model}')
if c.mode == 'azure':
    print(f'Deployment: {c.azure_deployment}')
"
```

Expected output examples:
- **Azure mode**: `Mode: azure` / `Model: gpt-4` / `Deployment: gpt-4`
- **Anthropic mode**: `Mode: anthropic` / `Model: claude-3-5-sonnet-20241022`
- **CLI mode**: `Mode: cli` / `Model: claude-opus-4.6`

## Priority Summary

The system uses this priority order:

1. ✅ **Azure OpenAI** - If all 4 env vars set + openai package installed
2. ✅ **Anthropic API** - If ANTHROPIC_API_KEY set + anthropic package installed  
3. ✅ **GitHub Copilot CLI** - Fallback if above not available

**Automatic fallback chain:** Azure → Anthropic → CLI (on errors)
