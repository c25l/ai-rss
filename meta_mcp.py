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
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from datetime import datetime
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from datetime import datetime, timedelta, timezone  
from dateutil import parser,tz
import subprocess

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
            name="get_events",
            description="get upcoming events from the calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar": {
                        "type": "string",
                        "description": "which calendar to query: one of 'orchestrator', 'personal', 'partner' or 'work'",
                    },
                    "days": {"type":"number",
                             "description": "how many days to look ahead for events",
                             "default": 7}
                },
                "required": ["calendar"]
            },
        ),
        Tool(
            name="align_calendars",
            description="make sure the start and end blocks on the personal calendar are aligned with the work calendar",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="recent_journal_entries",
            description="get the last week of journal entries for the user",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="open_todos",
            description="get all open todos for the user",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_news_feed",
            description="get the news feed articles from preconfigured feeds",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed": {
                        "type": "string",
                        "description": "which feedset to fetch. Options are 'news','culture','ai','local','research'. Default is 'news'",
                        "default": 'news'
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="subtask",
            description="get the results of a subtask, without carrying the context--will prompt a wholly new session, please give the instructions you'd want to receive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "subtask prompt to execute"
                    },
                },
                "required": ["prompt"]
            }
        )
    ]

def time_stuff(time_str: str) -> datetime:
    if "PDT" in time_str or "PST" in time_str:
        tzinfo = tz.gettz("America/Los_Angeles")
    elif "MDT" in time_str or "MST" in time_str:
        tzinfo = tz.gettz("America/Denver")
    elif "CDT" in time_str or "CST" in time_str:
        tzinfo = tz.gettz("America/Chicago")
    elif "EDT" in time_str or "EST" in time_str:
        tzinfo = tz.gettz("America/New_York")     
    else:
        tzinfo = tz.gettz("UTC")      
    time_str = parser.parse(time_str,tzinfos=[tzinfo])
    if time_str.tzinfo is None:
        time_str = time_str.replace(tzinfo=tzinfo)
    return time_str


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    # Dispatch to appropriate tool handler
    # Configuration
    outbox = StdioServerParameters(
        command = "/Users/chris/source/airss/venv/bin/python3", 
        args = ["/Users/chris/source/airss/outbox_mcp.py"], 
        cwd = '/Users/chris/source/airss', 
    )
    calendar=server_params = StdioServerParameters(
        command = '/opt/homebrew/bin/npx',  
        args = ["@cocal/google-calendar-mcp"], 
        env = {"GOOGLE_OAUTH_CREDENTIALS":"/Users/chris/source/airss/credentials.json"}
    )
    obsidian = StdioServerParameters(
        command = "/Users/chris/source/airss/venv/bin/uvx",  
        args = ["mcp-obsidian"], 
        env = {"OBSIDIAN_API_KEY": "66bfb78dd15826fa3cc22e0ffa4ed48ac2d1b685e9833f29aa950c1171336d82",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"} 
    )

    feeds = StdioServerParameters(
        command = "/Users/chris/source/airss/venv/bin/python3", 
        args = ["rss_mcp.py"], 
    )
    if name in ["outbox_add_document", "outbox_flush"]:
        async with stdio_client(outbox) as (read, write):
            async with ClientSession(
                read, write,
                ) as session:
                # Initialize the connection
                await session.initialize()
                if name == "outbox_add_document":
                    result= await session.call_tool("add", arguments=arguments)
                elif name == "outbox_flush":
                    result= await session.call_tool("send_all", arguments=arguments)
                result = result.content[0].text
    elif name in ["get_events", "align_calendars"]:
        async with stdio_client(calendar) as (read, write):
            async with ClientSession(
                read, write,
            ) as session:
                # Initialize the connection
                cals = {'orchestrator':"969a157ef1848f6ff639e8099d8ecd9b6b07f6c0f7f7d781b5c09e9ff8e738b8@group.calendar.google.com", 
                            'personal': "christopher.p.bonnell@gmail.com", 
                            'partner': "sharamdavis@gmail.com",
                            'work':"2i9i000osgrujeqnqfd9usotbr29dlpq@import.calendar.google.com"}
                await session.initialize()
                if name == "get_events":
                    if "calendar" not in arguments or arguments["calendar"] not in cals:
                        result = "Invalid calendar specified. Must be one of: 'orchestrator', 'personal', 'partner', 'work'"
                    else:
                        time = datetime.now()
                        time = time - timedelta(hours = time.hour, minutes=time.minute, seconds=time.second, microseconds=time.microsecond)
                        endtime = time + timedelta(days=arguments.get("days", 7)+1) - timedelta(seconds=1)
                        result= await session.call_tool("list-events", arguments={
                            "timeMin": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeMax": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeZone": "America/Denver",
                            "calendarId": cals[arguments["calendar"]]
                        })
                        result =result.content[0].text
                elif name == "align_calendars":
                        time = datetime.now()
                        time = time - timedelta(hours = time.hour, minutes=time.minute, seconds=time.second, microseconds=time.microsecond)
                        for ii in range(8):
                            usetime = time + timedelta(days=ii)
                            endtime = usetime + timedelta(days=1) - timedelta(seconds=1)
                            # Align personal calendar with work calendar
                            temp = await session.call_tool("list-events", arguments={
                            "timeMin": usetime.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeMax": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeZone": "America/Denver",
                            "calendarId": cals["work"]
                            })
                            temp = ["Event:" + xx for xx in temp.content[0].text.split("Event:")]
                            temp  = [[xx for xx in yy.split("\n") if "Start" in xx or "End" in xx or "Event: " in xx] for yy in temp] 
                            temp = [{zz[:zz.find(":")]: zz[zz.find(":")+1:].strip() for zz in xx if zz.find(":")>0} for xx in temp if len(xx) > 0] 
                            for zz in temp:
                                if "Start" in zz:
                                    zz["Start"] = time_stuff(zz["Start"])
                                if "End" in zz:                
                                    zz["End"] = time_stuff(zz["End"])
                                if "Start Date" in zz:
                                    zz["Start Date"] = parser.parse(zz["Start Date"])
                                if "End Date" in zz:
                                    zz["End Date"] = parser.parse(zz["End Date"])
                            temp_days=[xx for xx in temp if "Start" not in xx]
                            temp_days =[xx for xx in temp_days if xx["Event"]=="Away"]
                            temp_events = [xx for xx in temp if "Start" in xx]
                            personal = await session.call_tool("list-events", arguments={
                            "timeMin": usetime.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeMax": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
                            "timeZone": "America/Denver",
                            "calendarId": cals["personal"]})
                            personal = ["Event:" + xx for xx in personal.content[0].text.split("Event:")]
                            personal = [xx for xx in personal if xx.strip().startswith("Event: Start") or xx.strip().startswith("Event: End")]
                            personal = [{zz[:zz.find(":")]: zz[zz.find(":")+1:].strip() for zz in xx.split("\n") if zz.find(":")>0} for xx in personal if len(xx) > 0] 
                            for zz in personal:
                                if "Start" in zz:
                                    zz["Start"] = time_stuff(zz["Start"])
                                if "End" in zz:            
                                    zz["End"] = time_stuff(zz["End"])
                            for xx in personal:
                                if "Event ID" not in xx:
                                    continue
                                boop = await session.call_tool("delete-event", arguments={
                                "eventId": xx["Event ID"],
                                "calendarId": cals["personal"]
                                })
                            if temp_days or usetime.weekday() in [5,6]:
                                pass
                            else:
                                # no whole-day stuff.
                                location = usetime.replace(tzinfo=tz.gettz("America/Denver"))
                                dayend = location + timedelta(days=1) - timedelta(seconds=1)
                                start = min(temp_events, key=lambda x: x["Start"])["Start"]
                                start = min(start, location+timedelta(hours=9,minutes=30))
                                if start< location:
                                    start = location + timedelta(hours=9,minutes=30)
                                end = max(temp_events, key=lambda x: x["End"])["End"]
                                end = max(end, location+timedelta(hours=18,minutes=30))
                                if end> dayend:
                                    end  = location + timedelta(hours=18,minutes=30)
                                beep = await session.call_tool("create-event", arguments={
                                "calendarId": cals["personal"],
                                "summary": "Start",
                                "description":"",
                                "start" : start.isoformat(),
                                "end" : (start+timedelta(hours=1)).isoformat(),
                                "timeZone": "America/Denver"
                                })
                                beep = await session.call_tool("create-event", arguments={
                                "calendarId": cals["personal"],
                                "summary": "End",
                                "description":"",
                                "start" : (end - timedelta(hours=1)).isoformat(),
                                "end" : end.isoformat(),
                                "timeZone": "America/Denver"
                                })
                        result = "ok"
    elif name in ["recent_journal_entries","open_todos"]:
        async with stdio_client(obsidian) as (read, write):
            async with ClientSession(
                read, write,
            ) as session:
                # Initialize the connection
                await session.initialize()
                if name == "recent_journal_entries":
                    result = await session.call_tool("obsidian_get_recent_changes", arguments={"limit":20,"days":7})
                    files = json.loads(result.content[0].text)
                    files = [xx["filename"] for xx in files]
                    recent = []
                    for xx in files:
                        if "daily" not in xx.lower():
                            continue
                        temp = await session.call_tool("obsidian_get_file_contents", arguments={"filepath":xx})
                        temp = temp.content[0].text.split("\\n")
                        recent += [f"# {xx}"] + temp
                    result = "\n".join(recent)
                    
                elif name == "open_todos":
                    result = await session.call_tool("obsidian_complex_search", arguments={"query":{"regexp": ["- \\[ \\]",{"var":"content"}]}})
                    print(len(result.content))
                    files = [xx["filename"] for xx in json.loads(result.content[0].text)]
                    tasks = []
                    for xx in files:
                        temp = await session.call_tool("obsidian_get_file_contents", arguments={"filepath":xx})
                        temp = temp.content[0].text.split("\\n")
                        temp = [line.replace("- [ ] ","- ").replace("\\t","").strip() for line in temp if "- [ ]" in line]
                        tasks += temp
                    result = "\n".join(tasks)
    elif name == "get_news_feed":
        async with stdio_client(feeds) as (read, write):
            async with ClientSession(
                read, write,
            ) as session:
                feed_configs = {"news":["https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "https://www.theatlantic.com/feed/all/", "https://heathercoxrichardson.substack.com/feed"],
                                "culture":["https://rss.metafilter.com/metafilter.rss", "https://acoup.blog/feed/"],
                                "ai":["https://www.microsoft.com/en-us/research/feed/", "https://www.nature.com/nature.rss"],# "https://tldr.tech/api/rss/ai"],
                                "local":["https://www.longmontleader.com/rss/", "https://www.reddit.com/r/Longmont.rss"],
                                "research":["https://export.arxiv.org/rss/cs.AI","https://export.arxiv.org/rss/cs.Lg","https://export.arxiv.org/rss/stat.ML"]}
                # Initialize the connection
                await session.initialize()
                if "feed" not in arguments:
                    arguments["feed"] = "news"
                if "page" not in arguments:
                    arguments["page"] = 1
                
                limit = 20
                offset = limit*(arguments["page"]-1)
                result = await session.call_tool("get_articles", arguments={"feeds":feed_configs[arguments["feed"]], "limit":limit, "offset":offset,"days_back":1})
                print(dir(result))
                print("result length:", len(result.content))
                result = json.loads(result.content[0].text)
                print("here")
                print(arguments["feed"]+f" result: {len(result)}")
                result = "\n".join([f"- [{xx['title']}]({xx['url']})\n{xx['summary']}\n---\n" for xx in result["articles"]])
    elif name == "subtask":
        result = subprocess.run([
                        "/Users/chris/go/bin/mcphost",  
                        "--quiet",
                        "-p",
                        arguments['prompt'].replace('"', '\\"').replace("'", "\\'")
                    ], capture_output=True, text=True)
        result = result.stdout.split("</think>")[-1].strip()
    else:
        raise ValueError(f"Unknown tool name: {name}")
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
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
