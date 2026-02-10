# Quick Start: Azure OpenAI Setup

This guide helps you quickly configure h3lper to use your Azure OpenAI deployment.

## What You Need

From your Azure Portal → Azure OpenAI Service, gather these 4 values:

1. **Endpoint URL**: Found in "Keys and Endpoint" section
   - Format: `https://your-resource.openai.azure.com/`
   
2. **API Key**: Found in "Keys and Endpoint" section (KEY 1 or KEY 2)
   
3. **Deployment Name**: The name you gave your model deployment
   - This could be "gpt-4", "claude-35-sonnet", "my-gpt4-deployment", etc.
   - Found in "Deployments" section
   
4. **API Version**: Usually `2024-02-15-preview` (latest stable)

## Setup Steps

### 1. Create or edit your `.env` file

```bash
cd /home/runner/work/h3lper/h3lper
cp .env.example .env  # if .env doesn't exist
```

### 2. Add your Azure OpenAI credentials

Edit `.env` and add:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Replace:**
- `your-resource` with your actual Azure resource name
- `your_actual_api_key_here` with your KEY 1 or KEY 2 from Azure Portal
- `your_deployment_name` with your actual deployment name from Azure

### 3. Install the OpenAI package

```bash
pip install openai>=1.12.0
```

### 4. Test your configuration

```bash
python3 -c "
from copilot import Copilot
c = Copilot()
print(f'✓ Mode: {c.mode}')
print(f'✓ Model: {c.model}')
if c.mode == 'azure':
    print(f'✓ Deployment: {c.azure_deployment}')
    print('✓ Azure OpenAI is configured and ready!')
else:
    print(f'⚠ Not using Azure mode. Check your .env configuration.')
"
```

Expected output:
```
✓ Mode: azure
✓ Model: gpt-4
✓ Deployment: gpt-4
✓ Azure OpenAI is configured and ready!
```

## Common Issues

### Issue: "Mode: cli" instead of "Mode: azure"

**Possible causes:**
1. Missing one or more environment variables
2. Environment variables not loaded (make sure `.env` is in the right location)
3. OpenAI package not installed

**Solution:**
```bash
# Check if all 4 env vars are set
python3 -c "
import os
print('Endpoint:', 'SET' if os.getenv('AZURE_OPENAI_ENDPOINT') else 'NOT SET')
print('API Key:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET')
print('Deployment:', 'SET' if os.getenv('AZURE_OPENAI_DEPLOYMENT') else 'NOT SET')
print('API Version:', 'SET' if os.getenv('AZURE_OPENAI_API_VERSION') else 'NOT SET')
"

# Make sure openai package is installed
pip install openai
```

### Issue: "openai package not available"

**Solution:**
```bash
pip install openai>=1.12.0
```

### Issue: API errors when generating

**Possible causes:**
1. Wrong endpoint URL format
2. Invalid API key
3. Deployment name doesn't match Azure
4. Network connectivity issues

**Solution:**
1. Verify endpoint URL ends with `/`
2. Copy-paste API key directly from Azure Portal
3. Check deployment name matches exactly (case-sensitive)
4. Test connectivity: `curl -I https://your-resource.openai.azure.com/`

## What Deployment Should I Use?

h3lper works with any Azure OpenAI deployment:

- **GPT-4**: Best for complex reasoning and long context
- **GPT-4 Turbo**: Faster and cheaper than GPT-4
- **GPT-3.5 Turbo**: Fast and economical
- **Claude via Azure**: If you have Claude deployed through Azure

The system will automatically use whatever deployment you specify.

## Fallback Behavior

Even after setting up Azure OpenAI, the system maintains fallbacks:

1. **Primary**: Azure OpenAI (your configuration)
2. **Secondary**: Anthropic API (if `ANTHROPIC_API_KEY` is set)
3. **Tertiary**: GitHub Copilot CLI (if installed)

If Azure fails (quota, network issues, etc.), it automatically tries the other modes.

## Need Help?

See the full documentation in `LLM_CONFIG.md` for:
- Detailed configuration options
- Advanced troubleshooting
- Model selection guide
- Testing procedures
