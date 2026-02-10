# Citation Analysis Integration

This document describes the citation analysis feature that identifies the most-cited papers from recent arXiv submissions.

## Overview

The citation analysis system:
1. Fetches recent papers from arXiv RSS feeds (last 1-7 days)
2. Uses Semantic Scholar API to extract references from each paper
3. Builds a citation graph tracking which papers are cited by recent submissions
4. Ranks papers by citation count to identify foundational/important research
5. Displays top 15 papers on a dedicated tab in the static site

## Architecture

### Components

1. **citations_data.py** - Citation data management
   - `run_citation_analysis()` - Executes citation graph analysis
   - `save_citation_data()` / `load_citation_data()` - JSON persistence
   - `generate_and_save_citations()` - Main entry point for workflow

2. **daily_workflow_agent.py** - Workflow integration
   - Runs citation analysis after briefing generation
   - Always executes to keep data fresh
   - Continues even if analysis fails (non-blocking)

3. **publish_site.py** - Static site generation
   - `_citations_page()` - Generates HTML for citation rankings
   - Added "Citations" tab to navigation
   - Creates `/citations/index.html` during site generation

4. **research.py** - Citation analysis engine
   - `CitationRanker` class wraps ArxivCitationAnalyzer
   - Converts results to Article objects with citation metadata
   - Configurable categories, lookback days, and citation thresholds

5. **arxiv_citations.py** - Core citation graph analyzer
   - Fetches papers from arXiv RSS or API
   - Queries Semantic Scholar for paper references
   - Builds directed citation graph
   - Returns ranked papers with metadata

## Data Flow

```
Daily Workflow
     ↓
Run Citation Analysis (citations_data.py)
     ↓
Research.CitationRanker (research.py)
     ↓
ArxivCitationAnalyzer (arxiv_citations.py)
     ↓
Semantic Scholar API
     ↓
Citation Graph → Top N Papers
     ↓
Save to briefings/citations_latest.json
     ↓
Static Site Generation (publish_site.py)
     ↓
Display on /citations/ page
```

## Configuration

The citation analysis uses these default parameters (configurable in citations_data.py):

- **days**: 1 (look back 1 day for papers)
- **top_n**: 15 (return top 15 most-cited papers)
- **min_citations**: 1 (minimum citation threshold)
- **categories**: All research categories from preferences.yaml
  - AI/ML: cs.AI, cs.LG, cs.CL, cs.CV
  - Systems: cs.DC, cs.SY, cs.PF, cs.AR

## Output Format

Citation data is stored in `briefings/citations_latest.json`:

```json
{
  "generated_at": "2026-02-10T04:24:44.452264",
  "analysis_params": {
    "days": 1,
    "top_n": 15,
    "min_citations": 1,
    "categories": ["cs.AI", "cs.LG", ...]
  },
  "papers": [
    {
      "title": "Paper Title",
      "url": "https://arxiv.org/abs/...",
      "summary": "Paper abstract...",
      "published_at": "2023-01-01",
      "citation_count": 5,        // Citations from recent papers
      "total_citations": 1000     // Total citations (from Semantic Scholar)
    }
  ],
  "paper_count": 15
}
```

## Citations Page

The static site now includes a "Citations" tab showing:
- Title: "📊 Most Cited Papers"
- Description: "Papers most frequently cited by recent arXiv submissions"
- Timestamp: When the analysis was last run
- List of top 15 papers with:
  - Paper title (linked to arXiv)
  - Citation count from recent papers
  - Total citations from Semantic Scholar
  - Paper summary (truncated to 400 chars)

## Usage

### Manual Testing

Test citation analysis:
```bash
python citations_data.py
```

### Daily Workflow

Citation analysis runs automatically during daily workflow:
```bash
python daily_workflow_agent.py
```

The analysis:
- Runs after briefing generation
- Continues even if it fails (non-blocking)
- Updates `briefings/citations_latest.json`
- Is included in static site generation

### Viewing Results

After site generation, visit:
- **Local**: `/tmp/site_dir/citations/index.html`
- **Production**: `https://yoursite.github.io/citations/`

## Future Enhancements

As mentioned in the requirements, the system is designed to be expanded:

1. **Weekly aggregation** - Pool papers from a full week
2. **Incremental updates** - Cache citation data to avoid recomputing
3. **Historical tracking** - Show trends in citation patterns over time
4. **Category filtering** - Separate tabs for AI/ML vs Systems papers
5. **Network visualization** - Interactive citation graph display

## Dependencies

Required Python packages (already in requirements.txt):
- arxiv>=2.0.0
- semanticscholar>=0.8.0

## Troubleshooting

**No papers found:**
- Check arXiv RSS feed accessibility
- Verify categories in preferences.yaml
- Check network connectivity to export.arxiv.org

**API rate limiting:**
- Semantic Scholar API has rate limits
- Adjust `api_delay` parameter in ArxivCitationAnalyzer
- Consider using API key for higher limits

**Empty citations page:**
- Ensure citations_latest.json exists in briefings/
- Run `python citations_data.py` to generate test data
- Check console for error messages during site generation
