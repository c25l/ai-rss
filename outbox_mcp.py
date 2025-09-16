#!/usr/bin/env python3
"""
MCP Server: Enhanced Outbox Service  
Provides accumulative document building with add/send_all functionality
"""

import asyncio
import json
import os
import fcntl
import outbox
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from datetime import datetime

mcp_server = Server("email-service")

@mcp_server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="outbox://status",
            name="Outbox Service Status", 
            description="Current status of the outbox service",
            mimeType="application/json",
        ),
        Resource(
            uri="outbox://buffer",
            name="Current Buffer Content", 
            description="View current accumulated buffer content",
            mimeType="application/json",
        )
    ]

@mcp_server.list_resource_templates()
async def handle_list_resource_templates() -> list[Resource]:
    return []

@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    uri_str = str(uri)
    if uri_str == "outbox://status":
        buffer_data = outbox.load_buffer()
        status = {
            "service": "outbox",
            "status": "running",
            "buffer_length": len(buffer_data["accumulated_content"]),
            "current_subject": buffer_data["subject"],
            "last_updated": buffer_data["last_updated"],
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(status, indent=2)
    elif uri_str == "outbox://buffer":
        buffer_data = outbox.load_buffer()
        return json.dumps(buffer_data, indent=2)
    
    raise ValueError(f"Unknown resource: {uri_str}")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="send",
            description="place a document in the outbox to send its content",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "complete content to send"
                    },
                    "subject": {
                        "type": "string",
                        "description": "subject of sent content",
                        "default": f"📰 {datetime.now().strftime('%Y-%m-%d')}"
                    }
                },
                "required": ["content"]
            },
        ),
        Tool(
            name="add",
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
            name="send_all",
            description="send all accumulated buffer content and clear the buffer",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="clear",
            description="clear the accumulated buffer without sending",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]
async def tool_send(arguments: dict | None) -> dict:
    """Handle send tool - send content immediately"""
    if not arguments or "content" not in arguments:
        return {"status": "error", "message": "content parameter required"}
    
    markdown_content = arguments["content"]
    subject = arguments.get("subject", f"📰 AIRSS Newsletter - {datetime.now().strftime('%Y-%m-%d')}")
    
    return await send_email(markdown_content, subject)

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    # Dispatch to appropriate tool handler
    if name == "send":
        result = await tool_send(arguments)
    elif name == "add":
        result = await tool_add(arguments)
    elif name == "send_all":
        result = await tool_send_all(arguments)
    elif name == "clear":
        result = await tool_clear(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="outbox_service",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
