#!/usr/bin/env python3
"""
MCP Server: Enhanced Outbox Service  
Provides accumulative document building with add/send_all functionality
"""

import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import outbox
from modules import journal, news, research, weather, spaceweather, personal_summary

# Create FastMCP server
mcp = FastMCP("utilities")

@mcp.tool()
def outbox_add_document(content: str, subject: str = None) -> str:
    """Add content to the accumulated outbox buffer"""
    if subject is None:
        subject = f"📰 {datetime.now().strftime('%Y-%m-%d')}"
    result = outbox.add(content, subject)
    return json.dumps(result, indent=2)

@mcp.tool()
def outbox_flush(empty:dict) -> str:
    """Send all accumulated buffer content and clear the buffer"""
    result = outbox.send_all()
    return json.dumps(result, indent=2)

@mcp.resource("utilities://personal")
def get_personal_info() -> str:
    """Get upcoming events from the calendar, and recent journal entries"""
    result = personal_summary.PersonalSummary().pull_data()
    return json.dumps(result, indent=2)

@mcp.resource("utilities://news")
def get_news() -> str:
    """Get today's news"""
    result = news.News().pull_data()
    return json.dumps(result, indent=2)

@mcp.resource("utilities://research")
def get_research() -> str:
    """Get today's research preprints"""
    result = research.Research().pull_data()
    return json.dumps(result, indent=2)

@mcp.resource("utilities://weather")
def get_weather() -> str:
    """Get upcoming local weather"""
    result = weather.Weather().pull_data()
    return json.dumps(result, indent=2)

@mcp.resource("utilities://space_weather")
def get_space_weather() -> str:
    """Get upcoming space weather data"""
    result = spaceweather.SpaceWeather().pull_data()
    return json.dumps(result, indent=2)

@mcp.prompt(title="Daily_Workflow")
def daily_workflow() -> str:
    """Generate a comprehensive daily summary with news, research, and personal updates"""
    return """
You will be making a daily summary document divided by subtasks. 
The information you need will be provided by the utilities mcp server..
Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

## Subtask: Generate news intelligence brief from RSS sources.

You will be given several news sources in several sections. Your job is to synthesize these into a coherent narrative, focusing on major stories, cultural developments, AI/tech news, and local Longmont updates.

Get the news documents via news resource of utilities mcp server.
Get weather via weather resource of the utilities mcp server
Get space weather via space_weather resource of the utilities mcp server
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
[Local weather info (this can be raw html)]

### Space Weather
[Space weather info (this can be raw html)]
```

Please deliver the finished markdown document via `mcp__utilities__outbox_add_document` 

## Subtask: Personal Summary

Add a personal status update by gathering information from multiple sources.

You will be given calendar events, recent Obsidian materials, and open todos. Your job is to synthesize this into a coherent personal status update.
Get these via personal resource of the utilities mcp server. The output you will generate from these must include original url links from the source material if at all possible.

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
1. Use research resource of the utilities mcp server to collect today's paper preprints.
2. Iterate through these keeping the best 5.
3. **Build progressively**: Update your recommendations as you discover better papers later on.
4. Use the preferences below to filter and prioritize.
5. If there are no articles for a day, do nothing.

### Quality Filtering (Apply Rigorous Standards):
**REJECT papers with these red flags:**
- Performance claims without rigorous measurement methodology
- System designs without scalability analysis
- Missing resource utilization metrics or cost analysis
- Theoretical models disconnected from operational constraints
- Benchmarks on toy problems rather than production scale

**Accept only papers that:**
- Provide quantitative performance analysis with statistical rigor
- Address real bottlenecks in distributed systems
- Include failure mode analysis and reliability considerations
- Connect algorithmic choices to hardware/infrastructure implications

**Research Preferences:**
- distributed training and inference systems
- GPU memory management and optimization
- model serving and deployment infrastructure
- workload characterization and resource allocation
- performance modeling for ML systems

**Particular interest in**:
- system-level optimizations for transformer inference
- distributed computing patterns for large model training
- hardware-software co-design for ML workloads
- operational aspects of ML infrastructure at scale

**Not interested in**:
- pure algorithmic improvements without system implications
- single-GPU optimizations
- theoretical complexity without practical validation
- AGI, robotics, biology applications
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
