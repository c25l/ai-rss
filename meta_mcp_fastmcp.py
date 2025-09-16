#!/usr/bin/env python3
"""
MCP Server: Enhanced Outbox Service  
Provides accumulative document building with add/send_all functionality
"""

import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import outbox
from modules import journal, news, research, weather, spaceweather

# Create FastMCP server
mcp = FastMCP("utilities")

@mcp.resource("outbox://status")
def get_outbox_status() -> str:
    """Current status of the utilities meta-mcp service"""
    return json.dumps({
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "service": "utilities meta-mcp"
    })

@mcp.tool()
def outbox_add_document(content: str, subject: str = None) -> str:
    """Add content to the accumulated outbox buffer"""
    if subject is None:
        subject = f"📰 {datetime.now().strftime('%Y-%m-%d')}"
    result = outbox.add(content, subject)
    return json.dumps(result, indent=2)

@mcp.tool()
def outbox_flush() -> str:
    """Send all accumulated buffer content and clear the buffer"""
    result = outbox.send_all()
    return json.dumps(result, indent=2)

@mcp.tool()
def personal() -> str:
    """Get upcoming events from the calendar, and recent journal entries"""
    result = journal.Journal().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def news() -> str:
    """Get today's news"""
    result = news.News().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def research() -> str:
    """Get today's research preprints"""
    result = research.Research().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def weather() -> str:
    """Get upcoming local weather"""
    result = weather.Weather().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def space_weather() -> str:
    """Get upcoming space weather data"""
    result = spaceweather.SpaceWeather().pull_data()
    return json.dumps(result, indent=2)

@mcp.prompt()
def daily_workflow() -> str:
    """Generate a comprehensive daily summary with news, research, and personal updates"""
    return """
You will be making a daily summary document divided by subtasks. 
The information you need will be provided by the mcp server at `mcp__utilities`.
Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

## Subtask: Generate news intelligence brief from RSS sources.

You will be given several news sources in several sections. Your job is to synthesize these into a coherent narrative, focusing on major stories, cultural developments, AI/tech news, and local Longmont updates.

Get the news documents via `mcp__utilities__news`
Get weather via `mcp__utilities__weather`
Get space weather via `mcp__utilities__space_weather`
### Content Guidelines:
- Filter out anything to do with Trump, Israel sports, music, performances
- Synthesize articles into coherent narrative sections
- Create engaging headlines connecting related articles
- Links to actual articles are of the utmost importance. Every story should have at least one link.
  - **PRESERVE existing markdown links from source data** - do not create new titles that lose the URLs
  - If creating connecting headlines, include links to the source articles being discussed
- Use markdown with inline links: [article title](url)

### Output Requirements:
```markdown
## News Intelligence Brief

### US & World News
[Synthesized narratives of major stories with links]

### Cultural & Society
[Interesting cultural developments and discussions with links]

### AI & Technology
[Relevant AI/tech developments with links]

### Local Longmont
[Local news and community updates with links]

### Weather
[Local weather info]

### Space Weather
[Space weather info]
```

Please deliver the finished markdown document via `mcp__utilities__outbox_add_document`

## Subtask: Personal Summary

Add a personal status update by gathering information from multiple sources.

You will be given calendar events, recent Obsidian materials, and open todos. Your job is to synthesize this into a coherent personal status update.
Get these via `mcp__utilities__personal`. The output you will generate from these must include original url links from the source material if at all possible.

### Output Requirements:
- Review materials and integrate into a factual status briefing
- Focus on items needing attention, follow-up, or preparation

```markdown
## Personal Status Update

### This Week's Key Items
[Today's important items]

### Upcoming Week
[Next week's notable events and commitments]

### Action Items
[Open todos and items requiring attention]

### Recent Activity
[Relevant Obsidian materials from past week]
```
Deliver the finished document via `mcp__utilities__outbox_add_document`

## Subtask: Research report.
Progressive analysis of AI/ML papers from the last day. 
You will be given a list of research preprint abstracts. Your job is to filter these based on quality and relevance, rank them, 
and return the best 5.
### Paper Collection Strategy:
1. Use `mcp__utilities__research` to collect today's paper preprints.
2. Iterate through these keeping the best 5.
3. **Build progressively**: Update your recommendations as you discover better papers later on.
4. Use the preferences below to filter and prioritize.
5. If there are no articles for a day, do nothing.

### Quality Filtering (Apply Rigorous Standards):
**REJECT papers with these red flags:**
- Big claims without big evidence
- Vague mathematical formalism
- Missing baselines/comparisons
- Buzzword bingo (mixing unrelated trending fields)
- Prominent AI tool acknowledgments

**Accept only papers that:**
- Make testable, precisely stated claims
- Have logical mathematical connections
- Use proper experimental methodology
- Prioritize substance over jargon

**Research Preferences:**
- machine learning and computational linguistics
- large language models
- embeddings
- transformers
- statistical methodology. 

**Particular interest in**:
- the theoretical foundations of AI systems
- representation learning
- computer science with statistical applications.

**Not interested in**:
- AGI
- driving
- protein
- privacy

### Output Requirements:
  **PRESERVE existing markdown links from source data** - do not create new titles that lose the URLs
return a markdown formatted string with the following sections:
```markdown
## ArXiv Research Digest

### Top Papers (Analyzed [X] of [Y] total papers)
[Best 5 papers with abstracts and analysis]
```
Deliver the finished markdown document via `mcp__utilities__outbox_add_document`

## Final Step: Send the accumulated document
Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

"""

if __name__ == "__main__":
    mcp.run()
