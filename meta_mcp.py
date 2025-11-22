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
def outbox_flush(empty:dict={}) -> str:
    """Send all accumulated buffer content and clear the buffer"""
    result = outbox.send_all()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_personal_info(empty:dict={}) -> str:
    """Get upcoming events from the calendar, and recent journal entries"""
    result = personal_summary.PersonalSummary().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_news(empty:dict={}) -> str:
    """Get today's news"""
    result = news.News().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_research(empty:dict={}) -> str:
    """Get today's research preprints"""
    result = research.Research().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_weather(empty:dict={}) -> str:
    """Get upcoming local weather"""
    result = weather.Weather().pull_data()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_space_weather(empty:dict={}) -> str:
    """Get upcoming space weather data"""
    result = spaceweather.SpaceWeather().pull_data()
    return json.dumps(result, indent=2)

@mcp.prompt(title="Daily_Workflow")
def daily_workflow() -> str:
    """Generate a comprehensive daily summary with news, research, and personal updates"""
    return """
You will be making a daily summary document divided by subtasks. Please use a subagent for each subtask.
The information you need will be provided by the utilities mcp server..
Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

# Subtask 1: Generate news intelligence brief from RSS sources.
Your job is to generate a news briefing. 
There must be inline markdown links `[article title](url)` to the original sources for these articles.
Output Requirements:
- Weather
    - Based on utilities mcp weather tool
        - Please summarize the given html weather forecast concisely using emojis and symbols and numbers format.
        - I only want the weather for the next 3 days.
-Space Weather
    - Based on utilities mcp space_weather tool
        - Please analyze the given data to provide a concise summary of the current and upcoming space weather conditions.
        - Include any significant geomagnetic activity or solar events that may impact Earth.
        - Please use emojis and symbols but do not express completel thoughts, only data.
- News Intelligence Brief
    - Based on utilities mcp news tool.
    - At most 7 total stories -- articles may be combined into larger themes if needed
    - Please make these stories of interest if there are articles to substantiate them:
        - Epstein files
        - AI model developments
        - AI hardware developments
        - AI datacenter developments
        - Local Longmoont news
        - Astromony / Space news


- Please deliver the finished markdown document via `utilities mcp outbox_add_document` 
- Do not flush the outbox yourself, just add the document.

# Subtask 2: Personal Summary
output a personal status update based on `utilities mcp personal` tool.
- what projects have I been working on lately?
- Deliver the finished document via `utilities mcp outbox_add_document`
    - Do not flush the outbox yourself, just add the document.

# Subtask 3: Research Preprints Summary
Synthesize based on utilities mcp research tool.
I want at most 5 preprints, focusing on practical real world developments in training or inference of ai models at scale.
Submit the document to `utilities mcp outbox_add_document`
Please make sure to include inline markdown links `[article title](url)` to the original sources for these articles.
- Do not flush the outbox yourself, just add the document.


"""


if __name__ == "__main__":
    mcp.run()
3