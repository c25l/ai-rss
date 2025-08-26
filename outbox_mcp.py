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

mcp_server = Server("email-service")

# Configuration
BUFFER_FILE = "/Users/chris/source/airss/outbox_buffer.json"

def load_buffer():
    """Load the current buffer state from file"""
    if not os.path.exists(BUFFER_FILE):
        return {
            "accumulated_content": "",
            "subject": f"📰 {datetime.now().strftime('%Y-%m-%d')}",
            "last_updated": datetime.now().isoformat()
        }
    
    try:
        with open(BUFFER_FILE, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "accumulated_content": "",
            "subject": f"📰 {datetime.now().strftime('%Y-%m-%d')}",
            "last_updated": datetime.now().isoformat()
        }

def save_buffer(buffer_data):
    """Save buffer state to file with file locking"""
    with open(BUFFER_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(buffer_data, f, indent=2)
        f.flush()

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
        buffer_data = load_buffer()
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
        buffer_data = load_buffer()
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

def format_group_for_narrative(group_text, articles_data):
    """Format a single group for narrative generation"""
    articles_text = ""
    for article in articles_data:
        articles_text += f"- **{article['title']}** ({article['source']})\n"
        articles_text += f"  Summary: {article['summary']}\n"
        articles_text += f"  URL: {article['url']}\n\n"
    
    return f"## {group_text}\n\n{articles_text}"

async def send_email(markdown_content: str, subject: str) -> dict:
    """Helper function to send email"""
    try:
        # Convert markdown to HTML properly
        from markdown import markdown
        html_body = markdown(markdown_content, extensions=['extra', 'codehilite'])
        
        # Add proper HTML styling
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        strong {{ color: #2c3e50; }}
        em {{ color: #7f8c8d; }}
        hr {{ border: none; border-top: 2px solid #ecf0f1; margin: 30px 0; }}
        ul {{ margin: 15px 0; }}
        li {{ margin: 8px 0; }}
        blockquote {{ 
            border-left: 4px solid #3498db; 
            margin: 20px 0; 
            padding-left: 20px; 
            color: #7f8c8d; 
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
        # Email configuration
        import smtplib
        from email.message import EmailMessage
        
        sender = "christopherpbonnell@icloud.com"
        receiver = "christopherpbonnell+airss@gmail.com"
        password = "vqxh-oqrp-wjln-eagl"  # Should be environment variable
        
        # Create and send email
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(html_content, subtype="html")
        
        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(msg['From'], password)
            server.send_message(msg)
        
        return {
            "status": "sent",
            "message": "Email sent successfully",
            "recipient": receiver,
            "subject": subject,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def tool_send(arguments: dict | None) -> dict:
    """Handle send tool - send content immediately"""
    if not arguments or "content" not in arguments:
        return {"status": "error", "message": "content parameter required"}
    
    markdown_content = arguments["content"]
    subject = arguments.get("subject", f"📰 AIRSS Newsletter - {datetime.now().strftime('%Y-%m-%d')}")
    
    return await send_email(markdown_content, subject)

async def tool_add(arguments: dict | None) -> dict:
    """Handle add tool - add content to buffer"""
    if not arguments or "content" not in arguments:
        return {"status": "error", "message": "content parameter required"}
    
    content = arguments["content"]
    subject = arguments.get("subject", f"📰 {datetime.now().strftime('%Y-%m-%d')}")
    
    try:
        buffer_data = load_buffer()
        
        # If buffer is empty, set the subject
        if not buffer_data["accumulated_content"].strip():
            buffer_data["subject"] = subject
        
        # Add separator if buffer has content
        if buffer_data["accumulated_content"].strip():
            buffer_data["accumulated_content"] += "\n\n"
        
        # Append new content
        buffer_data["accumulated_content"] += content
        buffer_data["last_updated"] = datetime.now().isoformat()
        
        save_buffer(buffer_data)
        
        return {
            "status": "added",
            "message": f"Content added to buffer ({len(content)} chars)",
            "buffer_length": len(buffer_data["accumulated_content"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to add content: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def tool_send_all(arguments: dict | None) -> dict:
    """Handle send_all tool - send buffer and clear"""
    try:
        buffer_data = load_buffer()
        
        if not buffer_data["accumulated_content"].strip():
            return {
                "status": "error",
                "message": "No content in buffer to send",
                "timestamp": datetime.now().isoformat()
            }
        
        # Send the accumulated content
        result = await send_email(buffer_data["accumulated_content"], buffer_data["subject"])
        
        # Clear the buffer
        buffer_data["accumulated_content"] = ""
        buffer_data["last_updated"] = datetime.now().isoformat()
        save_buffer(buffer_data)
        
        result["message"] = f"Accumulated content sent and buffer cleared. {result['message']}"
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send accumulated content: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def tool_clear(arguments: dict | None) -> dict:
    """Handle clear tool - clear buffer without sending"""
    try:
        buffer_data = load_buffer()
        buffer_data["accumulated_content"] = ""
        buffer_data["last_updated"] = datetime.now().isoformat()
        save_buffer(buffer_data)
        
        return {
            "status": "cleared",
            "message": "Buffer cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear buffer: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

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
