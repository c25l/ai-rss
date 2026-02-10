# Quick Start Guide: arXiv Citation Graph Analyzer

## What It Does

Analyzes recent arXiv papers to find the most-cited papers - identifying the foundational work that today's research builds upon.

## Installation

```bash
pip install -r requirements.txt
# Installs: arxiv>=2.0.0, semanticscholar>=0.8.0
```

## Quick Usage

### Option 1: Standalone CLI

```bash
# Basic usage (default: cs.AI, cs.LG, cs.CL categories)
python arxiv_citations.py

# Custom categories and parameters
python arxiv_citations.py --categories cs.DC cs.AR --days 2 --top-n 15
```

### Option 2: Python Integration

```python
from research import Research

# Enable citation analysis
research = Research(use_citation_ranker=True)

# Get top 10 most-cited papers from last day
result = research.pull_data_with_citations(days=1, top_n=10)
print(result)
```

### Option 3: Direct API

```python
from arxiv_citations import ArxivCitationAnalyzer

analyzer = ArxivCitationAnalyzer()
results = analyzer.analyze(
    categories=['cs.AI', 'cs.LG'],
    days=1,
    top_n=10
)

output = analyzer.format_results(results)
print(output)
```

## Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `categories` | arXiv categories (e.g., cs.AI, cs.LG) | `['cs.AI', 'cs.LG', 'cs.CL']` |
| `days` | Days to look back | `1` |
| `top_n` | Number of top papers | `10` |
| `min_citations` | Min citation threshold | `2` |

## Example Output

```
# Most Cited Papers from Recent arXiv Submissions

## 1. Attention Is All You Need
- arXiv ID: 1706.03762
- Cited by recent papers: 12 times
- Total citations: 75,432

The dominant sequence transduction models are based on...

## 2. BERT: Pre-training of Deep Bidirectional Transformers
- arXiv ID: 1810.04805
- Cited by recent papers: 9 times
- Total citations: 42,108

We introduce a new language representation model...
```

## Use Cases

- 📚 **Literature Review** - Find key papers in a new research area
- 🔍 **Research Tracking** - Monitor trending foundational papers
- 📊 **Trend Analysis** - See what methods researchers are building on
- 🎯 **Quality Filter** - Use citations as signal vs just titles

## Getting Help

- See `ARXIV_CITATIONS.md` for comprehensive documentation
- Run `python demo_arxiv_citations.py` for examples
- Run `python arxiv_citations.py --help` for CLI options

## Troubleshooting

**No papers found?**
- Check network access to export.arxiv.org
- Try increasing `--days` parameter

**No citation data?**
- Ensure access to api.semanticscholar.org
- Get a free API key: https://www.semanticscholar.org/product/api

**Rate limits?**
- Add `--api-key YOUR_KEY` for higher limits
- Increase delay between calls

## API Keys (Optional)

Get higher rate limits with a free Semantic Scholar API key:

```bash
# CLI
python arxiv_citations.py --api-key YOUR_KEY

# Python
research = Research(
    use_citation_ranker=True,
    semantic_scholar_api_key="YOUR_KEY"
)
```

Free key: https://www.semanticscholar.org/product/api
