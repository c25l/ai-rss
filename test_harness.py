#!/usr/bin/env /Users/chris/source/airss/venv/bin/python3
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
async def main():

    utilities = StdioServerParameters(
        command = "/Users/chris/source/airss/venv/bin/python3", 
        args = ["/Users/chris/source/airss/meta_mcp.py"], 
        cwd = '/Users/chris/source/airss', 
    )


    async with stdio_client(utilities) as (read, write):
        async with ClientSession(
            read, write,
            ) as session:
            # Initialize the connection
            await session.initialize()
            result= await session.call_tool("get_news_feed", arguments={"content":"news"})
            print("Result from add tool:", result)

if __name__ == "__main__":
    asyncio.run(main())