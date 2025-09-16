#!/usr/bin/env python3
"""
MCP Server: Enhanced Outbox Service  
Provides accumulative document building with add/send_all functionality
"""

import asyncio
import json
import os
import fcntl
from typing import Any, Sequence
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource, Prompt, PromptArgument, GetPromptResult, PromptMessage
from datetime import datetime
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from datetime import datetime, timedelta, timezone  
from dateutil import parser,tz
import subprocess
import outbox
from modules import journal, news,research, weather, spaceweather
mcp_server = Server("utilities")

@mcp_server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="outbox://status",
            name="Utilities Service Status", 
            description="Current status of the utilities meta-mcp service",
            mimeType="application/json",
        ),
    ]

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="outbox_add_document",
            description="add content to the accumulated outbox buffer",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "content to add to the accumulated document"
                    },
                    "subject": {
                        "type": "string",
                        "description": "subject of sent content (only used if this is first add)",
                        "default": f"📰 {datetime.now().strftime('%Y-%m-%d')}"
                    }
                },
                "required": ["content"]
            },
        ),
        Tool(
            name="outbox_flush",
            description="send all accumulated buffer content and clear the buffer",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="personal",
            description="get upcoming events from the calendar, and recent journal entries",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="news",
            description="get today's news.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="research",
            description="get today's research preprints.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="weather",
            description="get upcoming local weather.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="space-weather",
            description="get upcoming space weather data.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
          ]
@mcp_server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="daily_workflow",
            description="Generate a comprehensive daily summary with news, research, and personal updates. Call with `{}`",
            arguments=[]
        ),
    ]

        
@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    # Ensure arguments is a dict, even if None is passed
    if arguments is None:
        arguments = {}
    
    result = ""
    if name == "outbox_add_document":
        result = outbox.add(arguments.get("content",""),arguments.get("subject",""))
    elif name == "outbox_flush":
        result = outbox.send_all()
    elif name == "personal":
        result = journal.Journal().pull_data()
    elif name == "research":
        result = research.Research().pull_data()
    elif name == "news":
        result = news.News().pull_data()
    elif name == "weather":
        result = weather.Weather().pull_data()
    elif name == "space-weather":
        result = spaceweather.SpaceWeather().pull_data()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    #print(await handle_call_tool("outbox_flush", {"content":"news"}))
    #print(await handle_call_tool("get_news_feed", {"feed":"research", "page":1}))
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="utilities",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(
                        prompts_changed=True,
                        tools_changed=True,
                        resources_changed=True,
                    ),
                    experimental_capabilities={},
                ),
            ),
        )
@mcp_server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
    if name == "daily_workflow":
        return GetPromptResult(
            description="Generate a comprehensive daily summary with news, research, and personal updates",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""
You will be making a daily summary document divided by subtasks. 
The information you need will be provided by the mcp server at `mcp__utilities`.
Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

## Subtask: Generate news intelligence brief from RSS sources.

You will be given several news sources in several sections. Your job is to synthesize these into a coherent narrative, focusing on major stories, cultural developments, AI/tech news, and local Longmont updates.

Get the news documents via `mcp__utilities__news`
Get weather via `mcp__utilities__weather`
Get space weather via `mcp__utilities__space-weather`
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
                    )
                )
            ]
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")
if __name__ == "__main__":
    asyncio.run(main())
