#!/usr/bin/env python3
"""
MCP Server 2: Newsletter Generation Service  
Takes clustered article groups and generates markdown newsletter content
"""

import asyncio
import json
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from datetime import datetime
import json

mcp_server = Server("email-service")

@mcp_server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="outbox://status",
            name="Outbox Service Status", 
            description="Current status of the outbox service",
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
        status = {
            "service": "outbox",
            "status": "running",
            #"smtp_server": "smtp.mail.me.com:587", 
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(status, indent=2)
    
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

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "send":
        if not arguments or "content" not in arguments:
            return [TextContent(type="text", text="Error: markdown_content parameter required")]
        
        markdown_content = arguments["content"]
        subject = arguments.get("subject", f"📰 AIRSS Newsletter - {datetime.now().strftime('%Y-%m-%d')}")
        
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
            
            return [TextContent(type="text", text=json.dumps({
                "status": "sent",
                "message": "Newsletter email sent successfully",
                "recipient": receiver,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="newsletter-generation-service",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
