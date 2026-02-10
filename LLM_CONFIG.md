# LLM Configuration Guide

This document explains how to configure the LLM backend for h3lper.

## Overview

h3lper supports two modes of operation for LLM calls:

1. **Anthropic API** (Recommended): Direct API calls to Anthropic's Claude models
2. **GitHub Copilot CLI** (Fallback): Uses the local `copilot` CLI command

## Configuration

### Option 1: Anthropic API (Recommended)

This is the preferred method as it's more reliable and doesn't depend on CLI availability.

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
   Default for API mode: `claude-3-5-sonnet-20241022`

### Option 2: GitHub Copilot CLI (Fallback)

If no API key is configured, the system automatically falls back to the CLI.

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
┌─────────────────────────┐
│ ANTHROPIC_API_KEY set?  │
└────────┬────────────────┘
         │
    ┌────▼────┐
    │   YES   │
    └────┬────┘
         │
    ┌────▼─────────────────────┐
    │ anthropic package OK?    │
    └────┬────────────────┬────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │   YES   │      │   NO    │
    └────┬────┘      └────┬────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │ API MODE│      │ CLI MODE│
    └─────────┘      └─────────┘
```

## Fallback Behavior

If API mode is selected but fails on the first attempt, the system automatically falls back to CLI mode for that request. This provides maximum reliability.

## Troubleshooting

### Issue: Hanging during research ranking

**Symptoms:** The system prints "generating from..." and then hangs indefinitely, showing escape sequences like `^[[B^[[A`.

**Solution:** This was caused by CLI mode not closing stdin. Fixed in this PR by adding `stdin=subprocess.DEVNULL`.

### Issue: API calls failing

**Symptoms:** Errors mentioning "Anthropic" or "API key".

**Solution:**
1. Verify your API key is correct
2. Check you have credits/usage available in your Anthropic account
3. Ensure the anthropic package is installed: `pip install anthropic`

### Issue: CLI not found

**Symptoms:** Errors about `/usr/local/bin/copilot` not being found.

**Solution:**
1. Install GitHub Copilot CLI
2. Or set `ANTHROPIC_API_KEY` to use API mode instead

## Model Selection

Different models have different characteristics:

| Model | Mode | Speed | Quality | Cost |
|-------|------|-------|---------|------|
| claude-3-5-sonnet-20241022 | API | Fast | High | $$ |
| claude-opus-4.6 | CLI | Varies | Very High | - |

You can override the default by setting `COPILOT_MODEL` in your `.env`.

## Testing Your Configuration

Run this test to verify your configuration:

```bash
python3 -c "
from copilot import Copilot
c = Copilot()
print(f'Mode: {'API' if c.use_api else 'CLI'}')
print(f'Model: {c.model}')
"
```

Expected output:
- With API key: `Mode: API` / `Model: claude-3-5-sonnet-20241022`
- Without API key: `Mode: CLI` / `Model: claude-opus-4.6`
