# LLM Configuration Guide

h3lper supports two LLM backends in priority order:

1. **Azure OpenAI** — preferred when configured (supports completions + embeddings)
2. **GitHub Copilot CLI** — fallback

## 1. Azure OpenAI (Recommended)

### Setup

1. Create an Azure OpenAI resource in the Azure Portal
2. Deploy at least one **completion model** (e.g., `gpt-5.2`)
3. Deploy an **embedding model** (e.g., `text-embedding-3-large`) for research paper clustering

### Configuration

Add to your `.env`:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-52               # completion model deployment name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large  # embedding model deployment name
```

### What it enables

- **Completions**: All LLM calls (ranking, briefing generation, clustering) use Azure OpenAI
- **Embeddings**: Research papers are embedded and clustered by semantic similarity (requires `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`)

### Testing

```bash
python3 -c "
from copilot import Copilot
c = Copilot()
print(f'Mode: {\"Azure\" if c.use_azure else \"CLI\"}')
print(f'Model: {c.model}')
print(f'Embeddings: {c.has_embeddings()}')
print(c.generate('Say hello in one word.'))
"
```

## 2. GitHub Copilot CLI (Fallback)

Used when Azure OpenAI env vars are not set.

### Prerequisites

```bash
which copilot
# Should show: /usr/local/bin/copilot (or similar)
```

### Configuration

```bash
COPILOT_MODEL=claude-opus-4.6
```

Default model: `claude-opus-4.6`

**Note:** Embeddings are not available in CLI mode. Research papers will be ranked using LLM-based ranking instead of embedding-based clustering.

## Research Paper Clustering

When Azure embeddings are configured, research papers go through an enhanced pipeline:

1. **Embed** — each paper's title + summary is embedded (batches of 20)
2. **Cluster** — agglomerative clustering with cosine distance groups similar papers
3. **Rank clusters** — LLM ranks clusters by importance/impact
4. **Select representatives** — LLM picks the single best paper from each cluster

Without embeddings, the system falls back to direct LLM-based ranking.

## Troubleshooting

### Hanging during generation

**Symptoms:** Prints "generating from..." and then hangs.

**Cause:** CLI not closing stdin. Fixed by `stdin=subprocess.DEVNULL` in the subprocess call.

### CLI not found

**Symptoms:** Errors about `/usr/local/bin/copilot` not being found.

**Solution:** Install the GitHub Copilot CLI.

### Azure connection errors

**Symptoms:** Repeated "Attempt N failed" messages with Azure errors.

**Solution:** Verify your endpoint URL, API key, and deployment names in `.env`. The system retries with exponential backoff (up to 10 attempts).
