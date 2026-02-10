# Citation Analysis Troubleshooting Guide

If your Citations page shows "No data available" or you're experiencing issues with citation analysis, this guide will help you diagnose and fix the problem.

## Common Issues

### 1. No Papers Found

**Symptoms:**
- Citations page shows "No papers found"
- Citation analysis completes but returns 0 papers

**Possible Causes:**
- arXiv RSS feeds are empty for the selected time period (1 day is very recent!)
- Network connectivity issues preventing access to arXiv
- No papers matched the minimum citation threshold

**Solutions:**

1. **Increase the lookback period** - Look back more days to find papers:
   ```python
   # In daily_workflow_agent.py, line ~140
   citation_data = generate_and_save_citations(days=7, top_n=15, min_citations=1)
   ```

2. **Lower the citation threshold**:
   ```python
   citation_data = generate_and_save_citations(days=1, top_n=15, min_citations=0)
   ```

3. **Try different categories** - Edit `citations_data.py` to change categories or test specific ones:
   ```python
   # Try just AI/ML categories
   categories = ["cs.AI", "cs.LG"]
   ```

### 2. Network/Connectivity Issues

**Symptoms:**
- Error messages mentioning "network" or "unreachable"
- RSS feed timeouts

**Solutions:**

1. **Check arXiv accessibility**:
   ```bash
   curl -I https://export.arxiv.org/rss/cs.AI
   ```

2. **Test with demo script** (has fallback to example data):
   ```bash
   python demo_arxiv_citations.py
   ```

3. **Check firewall/proxy settings** - Ensure your environment can reach:
   - `export.arxiv.org` (RSS feeds)
   - `api.semanticscholar.org` (citation data)

### 3. Missing Dependencies

**Symptoms:**
- ImportError or ModuleNotFoundError
- Errors mentioning "arxiv" or "semanticscholar"

**Solutions:**

1. **Install required packages**:
   ```bash
   pip install arxiv semanticscholar
   ```

2. **Or install all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 4. API Rate Limiting

**Symptoms:**
- Errors mentioning "rate limit" or "429"
- Analysis stops partway through

**Solutions:**

1. **Increase API delay** - Edit `citations_data.py` or `research.py`:
   ```python
   # In CitationRanker.rank(), increase api_delay
   results = self.analyzer.analyze(
       categories=self.categories,
       days=days,
       max_papers=50,
       top_n=target,
       min_citations=min_citations,
       api_delay=2.0  # Increase from default 0.5
   )
   ```

2. **Get Semantic Scholar API key** for higher rate limits:
   - Sign up at https://www.semanticscholar.org/product/api
   - Set API key in your code or environment

## Manual Testing

### Run citation analysis manually:

```bash
python citations_data.py
```

This will:
- Show detailed progress messages
- Display any errors encountered
- Save results to `briefings/citations_latest.json`

### Check what's in the JSON file:

```bash
cat briefings/citations_latest.json | python -m json.tool
```

Look for:
- `"paper_count": 0` - No papers found
- `"error": "..."` - Error message
- Empty `"papers": []` array

### Test the full workflow:

```bash
python daily_workflow_agent.py
```

Watch for the citation analysis section in the output.

## Diagnostic Commands

### Check if arXiv RSS feeds are accessible:

```bash
# Test single category
curl "https://export.arxiv.org/rss/cs.AI" | head -50

# Test combined categories (what citations_data.py uses)
curl "https://export.arxiv.org/rss/cs.AI+cs.LG+cs.CL+cs.CV+cs.DC+cs.SY+cs.PF+cs.AR" | head -50
```

### Verify dependencies:

```bash
python -c "import arxiv; import semanticscholar; print('Dependencies OK')"
```

### Check Semantic Scholar API:

```bash
curl "https://api.semanticscholar.org/v1/paper/arXiv:1706.03762" | python -m json.tool
```

## Understanding Parameters

### `days` (default: 1)
- Number of days to look back for papers
- **Too low**: Very recent papers may not be in RSS feeds yet
- **Recommended**: 2-7 days for better results

### `top_n` (default: 15)
- Number of papers to display
- This is the maximum, you may get fewer

### `min_citations` (default: 1)
- Minimum citations from recent papers
- **Too high**: May exclude all papers
- **Recommended**: Start with 0 or 1

### `categories` (default: 8 categories)
- cs.AI, cs.LG, cs.CL, cs.CV (AI/ML)
- cs.DC, cs.SY, cs.PF, cs.AR (Systems)
- **More categories**: More papers to analyze but slower
- **Fewer categories**: Faster but may miss important papers

## Still Not Working?

1. **Check the demo script** - It has better error messages:
   ```bash
   python demo_arxiv_citations.py
   ```

2. **Use example mode** to verify the page renders correctly:
   ```bash
   python demo_arxiv_citations.py --example
   ```

3. **Look at logs** during daily workflow run for detailed error messages

4. **Check CITATIONS_INTEGRATION.md** for architecture details

## Quick Fixes for Common Scenarios

### "I just want to see if it works"
```python
# Edit daily_workflow_agent.py line ~140:
citation_data = generate_and_save_citations(days=7, top_n=15, min_citations=0)
```

### "Analysis runs but finds nothing"
- Increase `days` to 7-14
- Set `min_citations=0`
- Check network connectivity to arXiv

### "It's too slow"
- Reduce number of categories
- Reduce `top_n` 
- Increase `api_delay` if getting rate limited

### "RSS feeds seem blocked"
- Try using arXiv API mode (requires arxiv package)
- Check firewall/proxy settings
- Use demo mode as fallback
