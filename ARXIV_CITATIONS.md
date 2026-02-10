# ArXiv Citation Graph Analyzer

This feature analyzes recent arXiv papers and builds a directed citation graph to identify the most influential papers based on what today's researchers are citing.

## Problem Statement

Many arXiv papers may be wrong or retracted, but their citations are usually reliable. By analyzing which papers are most frequently cited by today's arXiv submissions, we can identify the important foundational papers that current research is building upon.

## How It Works

1. **Fetch Recent Papers**: Retrieves papers from arXiv submitted in the last N days (using RSS feeds or arXiv API)
2. **Extract Citations**: For each paper, extracts references using the Semantic Scholar API
3. **Build Citation Graph**: Creates a directed graph where edges point from citing papers to cited papers
4. **Calculate In-Degree**: Computes how many times each paper is cited by recent submissions
5. **Rank and Return**: Returns the papers with the highest citation counts

## Architecture

### Components

- **`arxiv_citations.py`**: Core citation analysis module
  - `ArxivCitationAnalyzer`: Main analyzer class
  - Supports both RSS feeds and arXiv API for fetching papers
  - Uses Semantic Scholar API for citation extraction
  - Gracefully handles missing dependencies and network issues

- **`research.py`**: Integration with existing research workflow
  - `CitationRanker`: New ranker class that uses citation analysis
  - Integrates seamlessly with existing `RelevanceRanker` and `NoveltyImpactRanker`

### Dependencies

```bash
pip install arxiv>=2.0.0
pip install semanticscholar>=0.8.0
```

These are added to `requirements.txt`.

## Usage

### Standalone CLI

```bash
# Basic usage (uses RSS feeds by default)
python arxiv_citations.py --categories cs.AI cs.LG --days 1 --top-n 10

# Use arXiv API instead of RSS (requires full network access)
python arxiv_citations.py --use-api --categories cs.DC --days 2 --top-n 15

# With Semantic Scholar API key for higher rate limits
python arxiv_citations.py --api-key YOUR_KEY --categories cs.AI --days 1

# Adjust minimum citation threshold
python arxiv_citations.py --min-citations 3 --days 2
```

### Integration with Research Module

```python
from research import Research

# Enable citation ranker
research = Research(use_citation_ranker=True)

# Run citation analysis
result = research.pull_data_with_citations(
    days=1,           # Look at papers from last 1 day
    top_n=10,         # Return top 10 cited papers
    min_citations=2   # Minimum 2 citations required
)

print(result)
```

### With Semantic Scholar API Key

```python
from research import Research

# Pass API key for higher rate limits
research = Research(
    use_citation_ranker=True,
    semantic_scholar_api_key="your_api_key_here"
)

result = research.pull_data_with_citations(days=2, top_n=15)
```

## Example Output

```markdown
# Most Cited Papers from Recent arXiv Submissions
*Analysis of papers submitted in the last 1 day(s)*

## 1. [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- **Cited by recent papers**: 8 times
- **Total citations**: 75432

This paper introduces the Transformer architecture, which relies entirely on 
attention mechanisms, dispensing with recurrence and convolutions...

## 2. [BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805)
- **Cited by recent papers**: 6 times
- **Total citations**: 42108

We introduce a new language representation model called BERT, which stands for 
Bidirectional Encoder Representations from Transformers...
```

## Configuration

### arXiv Categories

Common categories to analyze:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CL` - Computation and Language
- `cs.CV` - Computer Vision
- `cs.DC` - Distributed, Parallel, and Cluster Computing
- `cs.SY` - Systems and Control
- `cs.PF` - Performance
- `cs.AR` - Hardware Architecture

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `categories` | List of arXiv categories | `['cs.AI', 'cs.LG', 'cs.CL']` |
| `days` | Days to look back | `1` |
| `max_papers` | Max papers to fetch | `50` (API mode only) |
| `top_n` | Number of top papers to return | `10` |
| `min_citations` | Minimum citation threshold | `2` |
| `api_delay` | Delay between API calls (seconds) | `0.5` |

## Network Requirements

### RSS Mode (Default)
- Requires access to `export.arxiv.org` for RSS feeds
- Requires access to `api.semanticscholar.org` for citations
- More reliable in restricted network environments

### API Mode (Optional)
- Requires access to `export.arxiv.org` for arXiv API
- Requires access to `api.semanticscholar.org` for citations
- Use `--use-api` flag to enable

## Rate Limits

### Semantic Scholar API
- **Without API key**: 1 request per second, 100 requests per 5 minutes
- **With API key**: 10 requests per second, higher daily limits

Get a free API key at: https://www.semanticscholar.org/product/api

### Best Practices
- Use the default `api_delay=0.5` to respect rate limits
- For large analyses, consider getting a Semantic Scholar API key
- The analyzer automatically handles errors and continues processing

## Limitations

1. **Citation Data**: Only papers indexed by Semantic Scholar will have citation data
2. **arXiv References Only**: Only citations to other arXiv papers are counted (not papers in journals, conferences, etc.)
3. **Network Dependent**: Requires external API access for citation extraction
4. **Processing Time**: Fetching citations for 50 papers takes ~30-60 seconds with rate limiting

## Future Enhancements

Potential improvements:
- [ ] Cache citation data to reduce API calls
- [ ] Support citations from non-arXiv sources
- [ ] Add citation network visualization
- [ ] Integrate with existing research batches in `preferences.yaml`
- [ ] Add temporal analysis (trending papers over time)
- [ ] Support for co-citation analysis (papers cited together)

## Troubleshooting

### No papers fetched
- Check network access to `export.arxiv.org`
- Verify the categories are correct
- Try increasing `days` parameter

### No citation data
- Ensure access to `api.semanticscholar.org`
- Check if papers are indexed by Semantic Scholar
- Verify arXiv IDs are being extracted correctly

### Rate limit errors
- Increase `api_delay` parameter
- Get a Semantic Scholar API key
- Reduce `max_papers` parameter

## References

- [arXiv API](https://info.arxiv.org/help/api/index.html)
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [arxiv.py Python Library](https://github.com/lukasschwab/arxiv.py)
- [semanticscholar Python Library](https://github.com/danielnsilva/semanticscholar)
