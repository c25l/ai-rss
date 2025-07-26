#!/usr/bin/env python3
"""
MCP Server 3: SSE Coordination & Orchestration Service
Runs constantly, coordinates scheduling, provides workflow instructions to Claude
Email functionality is handled by Server 2, data fetching by Server 1
"""

import asyncio
import json
from typing import Any, Sequence, Set
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from datetime import datetime, timedelta
import threading
import time
import sys
from dataclasses import asdict
from orchestrator_config import get_config, reload_config
from simple_cron import SimpleCron
from orchestrator_db import get_db
from aiohttp import web
import aiohttp_cors
import queue

mcp_server = Server("orchestration-service")

# Global state for orchestration
workflow_status = {
    "current_stage": "idle",
    "progress": 0.0,
    "message": "Service ready",
    "last_run": None,
    "next_scheduled_run": None
}

# SSE Server components
sse_clients: Set[web.StreamResponse] = set()
sse_event_queue = queue.Queue()
sse_app = None
sse_server_task = None

# MCP Client connections
mcp_clients = {}

# Removed complex MCP client code - Claude handles MCP orchestration directly
scheduled_jobs = []  # Store scheduled cron jobs

@mcp_server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="orchestrator://status",
            name="Orchestrator Status",
            description="Current status of the orchestration service",
            mimeType="application/json",
        ),
        Resource(
            uri="orchestrator://workflow",
            name="Current Workflow Status", 
            description="Status of the current or last workflow run",
            mimeType="application/json",
        )
    ]

@mcp_server.list_resource_templates()
async def handle_list_resource_templates() -> list[Resource]:
    return []

@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    uri_str = str(uri)
    if uri_str == "orchestrator://status":
        status = {
            "service": "orchestration-service",
            "status": "running",
            "active_sse_clients": len(sse_clients),
            "scheduled_jobs": len(scheduled_jobs),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(status, indent=2)
    
    elif uri_str == "orchestrator://workflow":
        return json.dumps(workflow_status, indent=2)
    
    raise ValueError(f"Unknown resource: {uri_str}")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="trigger_workflow",
            description="Manually trigger the complete AIRSS workflow",
            inputSchema={
                "type": "object",
                "properties": {
               }
            },
        ),
        Tool(
            name="schedule_workflow",
            description="Schedule automatic workflow runs",
            inputSchema={
                "type": "object",
                "properties": {
                    "cron_expression": {
                        "type": "string",
                        "description": "Cron-like schedule (e.g., '0 6 * * *' for daily at 6am)"
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable or disable the schedule",
                        "default": True
                    }
                },
                "required": ["cron_expression"]
            },
        ),
        Tool(
            name="get_workflow_history",
            description="Get history of recent workflow runs",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of recent runs to return",
                        "default": 10
                    }
                }
            },
        ),
        Tool(
            name="send_sse_event",
            description="Send Server-Sent Event to connected clients",
            inputSchema={
                "type": "object", 
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Type of event (e.g., 'workflow:started', 'feeds:complete')"
                    },
                    "data": {
                        "type": "object",
                        "description": "Event data payload"
                    }
                },
                "required": ["event_type", "data"]
            },
        ),
        Tool(
            name="start_sse_server",
            description="Start the SSE server for real-time updates",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {
                        "type": "number",
                        "description": "Port to run SSE server on",
                        "default": 8080
                    }
                }
            },
        ),
        Tool(
            name="get_claude_orchestration_prompt",
            description="Get the complete prompt for Claude to orchestrate the AIRSS workflow using MCP servers",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        )
    ]

async def send_sse_event_to_client(response: web.StreamResponse, event_type: str, data: dict):
    """Send an event to a specific SSE client"""
    try:
        event_data = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        await response.write(event_data.encode())
    except Exception as e:
        print(f"[SSE] Failed to send to client: {e}")
        raise

def send_sse_event(event_type: str, data: dict):
    """Queue an SSE event to be sent to all clients"""
    global sse_event_queue
    event_data = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    sse_event_queue.put((event_type, event_data))
    print(f"[SSE] Queued event: {event_type} - {len(sse_clients)} clients")

async def broadcast_sse_event(event_type: str, data: dict):
    """Immediately broadcast an SSE event to all connected clients"""
    global sse_clients
    if not sse_clients:
        print(f"[SSE] No clients connected for event: {event_type}")
        return
    
    print(f"[SSE] Broadcasting {event_type} to {len(sse_clients)} clients")
    
    # Send to all clients
    disconnected = set()
    for client in sse_clients.copy():
        try:
            await send_sse_event_to_client(client, event_type, data)
        except Exception as e:
            print(f"[SSE] Failed to send to client, marking for removal: {e}")
            disconnected.add(client)
    
    # Remove disconnected clients
    sse_clients -= disconnected

# Complex workflow execution removed - this is now handled by Claude via MCP orchestration
# The orchestrator only coordinates and provides instructions

# Email sending removed - this is now handled by Server 2 via MCP calls

def cron_scheduler():
    """Background thread for scheduled workflows using proper cron expressions"""
    print(f"[CRON] Scheduler thread started at {datetime.now()}")
    
    while True:
        try:
            config = get_config()
            now = datetime.now()
            
            # Debug: Log every 5 minutes to show the thread is alive
            if now.minute % 5 == 0 and now.second < 5:
                print(f"[CRON] Scheduler alive at {now.strftime('%H:%M:%S')} - Schedule: {config.schedule.default_cron} - Enabled: {config.schedule.enabled}")
            
            if not config.schedule.enabled:
                time.sleep(60)
                continue
                
            cron = SimpleCron(config.schedule.default_cron)
            
            # Debug: Log when we're checking times
            if now.second == 0:  # Log once per minute
                print(f"[CRON] Checking {now.strftime('%H:%M')} against {config.schedule.default_cron} - Match: {cron.matches(now)}")
            
            # Check if current time matches the cron expression
            if cron.matches(now):
                # Check if we haven't run recently (avoid duplicate triggers)
                if (workflow_status["last_run"] is None or 
                    (now - datetime.fromisoformat(workflow_status["last_run"])).total_seconds() > 3600):  # 1 hour cooldown
                    
                    print(f"[CRON] Triggering workflow: {now.isoformat()}")
                    print(f"[CRON] Cron expression: {config.schedule.default_cron}")
                    
                    # Start workflow history tracking
                    workflow_id = now.strftime('%Y%m%d_%H%M%S')
                    db = get_db()
                    workflow_run = db.start_workflow(workflow_id, "cron")
                    
                    # Calculate next run time
                    try:
                        next_scheduled = cron.next_run(now)
                        workflow_status["next_scheduled_run"] = next_scheduled.isoformat()
                    except Exception as e:
                        print(f"[CRON] Warning: Could not calculate next run: {e}")
                        workflow_status["next_scheduled_run"] = None
                    
                    # Set workflow trigger flag for Claude to detect
                    workflow_status.update({
                        "current_stage": "triggered",
                        "progress": 0.0,
                        "message": "Cron triggered - ready for Claude orchestration",
                        "trigger_time": now.isoformat(),
                        "trigger_type": "cron",
                        "cron_expression": config.schedule.default_cron,
                        "workflow_id": workflow_id,
                        "run_id": workflow_run.run_id
                    })
                    
                    # Update history
                    db.update_workflow(workflow_run.run_id,
                                     stage="triggered",
                                     message="Cron triggered - ready for Claude orchestration")
                    
                    # Send SSE event to notify any connected Claude instances
                    if config.sse.enabled:
                        send_sse_event("cron:triggered", {
                            "time": now.isoformat(),
                            "cron_expression": config.schedule.default_cron,
                            "next_run": workflow_status.get("next_scheduled_run"),
                            "message": "Scheduled workflow trigger activated",
                            "instruction": "Use get_claude_orchestration_prompt to begin workflow"
                        })
                    
                    next_run_str = workflow_status.get("next_scheduled_run", "unknown")
                    print(f"[CRON] Trigger activated - Next run: {next_run_str}")
                
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"[CRON] Error in scheduler: {e}")
            time.sleep(60)

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "trigger_workflow":
        try:
            send_email = arguments.get("send_email", True) if arguments else True
            
            # Check configuration
            config = get_config()
            
            # Start workflow history tracking
            workflow_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            db = get_db()
            workflow_run = db.start_workflow(workflow_id, "manual")
            
            # Update workflow status
            workflow_status.update({
                "current_stage": "delegated_to_claude",
                "progress": 0.0,
                "message": "Workflow delegated to Claude for MCP orchestration",
                "last_run": datetime.now().isoformat(),
                "workflow_id": workflow_id,
                "run_id": workflow_run.run_id,
                "send_email": send_email
            })
            
            # Update history
            db.update_workflow(workflow_run.run_id, 
                             stage="delegated_to_claude",
                             message="Workflow delegated to Claude for MCP orchestration")
            
            # Send SSE event
            if config.sse.enabled:
                send_sse_event("workflow:delegated", {
                    "workflow_id": workflow_id,
                    "message": "Claude should now orchestrate the MCP workflow",
                    "send_email": send_email,
                    "timeout_seconds": config.workflow.timeout_seconds
                })
            
            # Pure coordination response - tell Claude exactly what to do
            instructions = f"""🤖 **AIRSS Workflow Orchestration Instructions**

Claude, please execute the following workflow steps:

**Step 1: Fetch & Cluster Articles**
- Call: `mcp__rss-clustering__get_clustered_articles` with `hours_back: {config.workflow.default_hours_back}`
- This will return grouped articles by topic

**Step 2: Generate Newsletter Content**
- Create an engaging newsletter from the clustered groups
- Use format: "📰 AIRSS Newsletter - {datetime.now().strftime('%Y-%m-%d')}"
- Organize by topic clusters with article summaries

**Step 3: {"Send Newsletter Email" if send_email else "Display Newsletter Only"}**
{f"- Call: `mcp__newsletter-generation__send_newsletter_email`" if send_email else "- Display the newsletter content (no email)"}
{f"- Subject: '📰 AIRSS Newsletter - {datetime.now().strftime('%Y-%m-%d')}'" if send_email else ""}

**Workflow ID:** {workflow_id}
**Triggered:** {datetime.now().isoformat()}
**Timeout:** {config.workflow.timeout_seconds} seconds

Please execute these steps now and report when complete."""

            return [TextContent(type="text", text=instructions)]
        
        except Exception as e:
            error_msg = f"Error in trigger_workflow: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            # Update workflow status with error
            workflow_status.update({
                "current_stage": "error",
                "progress": 0.0,
                "message": error_msg,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return [TextContent(type="text", text=json.dumps({
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }, indent=2))]
    
    elif name == "schedule_workflow":
        if not arguments or "cron_expression" not in arguments:
            return [TextContent(type="text", text="Error: cron_expression required")]
        
        cron_expr = arguments["cron_expression"]
        enabled = arguments.get("enabled", True)
        
        try:
            # Validate cron expression
            if not SimpleCron.is_valid(cron_expr):
                raise ValueError("Invalid cron expression")
            
            # Update configuration
            config = get_config()
            config.schedule.default_cron = cron_expr
            config.schedule.enabled = enabled
            
            # Calculate next run time
            now = datetime.now()
            cron = SimpleCron(cron_expr)
            next_run = cron.next_run(now)
            
            # Update workflow status
            workflow_status["next_scheduled_run"] = next_run.isoformat()
            
            # Store schedule
            schedule_config = {
                "cron": cron_expr,
                "enabled": enabled,
                "created": datetime.now().isoformat(),
                "next_run": next_run.isoformat()
            }
            
            scheduled_jobs.append(schedule_config)
            
            return [TextContent(type="text", text=json.dumps({
                "status": "scheduled",
                "cron_expression": cron_expr,
                "enabled": enabled,
                "next_run": next_run.isoformat(),
                "message": f"Workflow scheduled: {cron_expr}"
            }, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Failed to schedule workflow: {str(e)}",
                "cron_expression": cron_expr
            }, indent=2))]

    elif name == "get_workflow_history":
        try:
            limit = arguments.get("limit", 10) if arguments else 10
            
            db = get_db()
            recent_runs = db.get_recent_workflows(limit)
            
            # Convert to serializable format
            history_data = [asdict(run) for run in recent_runs]
            
            # Get statistics
            stats = db.get_workflow_stats(7)  # Last 7 days
            
            return [TextContent(type="text", text=json.dumps({
                "history": history_data,
                "count": len(history_data),
                "statistics": stats
            }, indent=2, default=str))]
            
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Failed to get workflow history: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2))]
    
    elif name == "send_sse_event":
        if not arguments or "event_type" not in arguments or "data" not in arguments:
            return [TextContent(type="text", text="Error: event_type and data required")]
        
        # Queue the event for broadcast
        send_sse_event(arguments["event_type"], arguments["data"])
        
        # Also broadcast immediately if there are connected clients
        if sse_clients:
            await broadcast_sse_event(arguments["event_type"], arguments["data"])
        
        return [TextContent(type="text", text=json.dumps({
            "status": "sent",
            "event_type": arguments["event_type"],
            "clients_notified": len(sse_clients)
        }, indent=2))]
    
    elif name == "start_sse_server":
        port = arguments.get("port", 8080) if arguments else 8080
        
        global sse_server_task
        if sse_server_task is None or sse_server_task.done():
            # Start the SSE server
            sse_server_task = asyncio.create_task(start_sse_http_server(port))
            
            return [TextContent(type="text", text=json.dumps({
                "status": "started",
                "message": f"SSE server started on port {port}",
                "endpoints": {
                    "events": f"http://localhost:{port}/events",
                    "status": f"http://localhost:{port}/status"
                }
            }, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "status": "already_running",
                "message": f"SSE server already running on port {port}"
            }, indent=2))]
    
    elif name == "get_claude_orchestration_prompt":
        prompt = f"""
# AIRSS Newsletter Generation Workflow

You are now acting as the orchestrator for the AIRSS (AI RSS Service) newsletter system. Your job is to coordinate the complete workflow using the available MCP servers to generate and send a news intelligence brief.

## Your Task:
1. **Fetch and cluster articles** using the RSS Clustering Service
2. **Enhance the clustering** with better group names for newsletter appeal  
3. **Generate engaging newsletter content** using the Newsletter Generation Service
4. **Send the final newsletter** via email

## Available MCP Servers:

### RSS Clustering Service (`rss-clustering`)
- `get_clustered_articles()` - Returns mathematically clustered article groups (pull server)

### Email Service (`email-service`)
- `send_newsletter_email(markdown_content)` - Sends newsletter via email (push server)

### Orchestration Service (`orchestration`)
- `send_sse_event()` - Send status updates (push server)
- Runs constantly and triggers workflows at 6am with cron

## Workflow Steps:

1. **Start workflow (triggered at 6am or manually):**
   ```
   send_sse_event("workflow:started", {{"timestamp": "{datetime.now().isoformat()}", "triggerType": "cron"}})
   ```

2. **Get clustered articles from Server 1:**
   ```
   groups_data = get_clustered_articles()  # Pull: Server 1 returns clustered groups
   ```

3. **Claude writes engaging newsletter** from the clustered groups:
   - Synthesize articles into coherent narrative sections
   - Create engaging headlines and stories that connect related articles  
   - Use markdown formatting with inline links: [article title](url)
   - Write as a complete intelligence brief

4. **Send the newsletter via Server 2:**
   ```
   send_newsletter_email(your_newsletter_markdown)  # Push: Server 2 sends email
   ```

5. **Send completion event:**
   ```
   send_sse_event("workflow:complete", {{"summary": {{"emailSent": true}}}})
   ```

## Your Writing Style:
- Create **engaging, coherent narratives** that connect related articles
- Write **concise but informative** content suitable for a daily intelligence brief
- Use **markdown formatting** with proper headers and inline links
- **Synthesize information** rather than just summarizing individual articles
- Focus on **meaningful analysis and context** between stories

## Email Details:
- The newsletter will be automatically sent to: christopherpbonnell+airss@gmail.com
- Subject: "📰 AIRSS Newsletter - [Today's Date]" 
- Format: Markdown converted to HTML for email

**Start the workflow now by calling the MCP tools in sequence!**
        """
        
        return [TextContent(type="text", text=prompt)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def sse_handler(request):
    """Handle SSE client connections"""
    global sse_clients, sse_event_queue
    
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )
    
    await response.prepare(request)
    sse_clients.add(response)
    
    print(f"[SSE] Client connected from {request.remote}. Total clients: {len(sse_clients)}")
    
    try:
        # Send initial connection event
        await send_sse_event_to_client(response, "connection", {
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "client_count": len(sse_clients)
        })
        
        # Keep connection alive and send queued events
        while True:
            try:
                # Check for events in queue
                try:
                    event_type, data = sse_event_queue.get_nowait()
                    await send_sse_event_to_client(response, event_type, data)
                except queue.Empty:
                    pass
                
                # Send heartbeat every 30 seconds
                await send_sse_event_to_client(response, "heartbeat", {
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[SSE] Client connection error: {e}")
                break
                
    finally:
        sse_clients.discard(response)
        print(f"[SSE] Client disconnected. Total clients: {len(sse_clients)}")
        
    return response

async def sse_status_handler(request):
    """Return SSE server status"""
    status = {
        "server": "AIRSS SSE Server",
        "status": "running",
        "port": request.host.split(':')[-1] if ':' in request.host else 8080,
        "connected_clients": len(sse_clients),
        "timestamp": datetime.now().isoformat()
    }
    return web.json_response(status)

async def start_sse_http_server(port=8080):
    """Start the HTTP SSE server"""
    global sse_app
    
    sse_app = web.Application()
    
    # Add CORS
    cors = aiohttp_cors.setup(sse_app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Add routes
    sse_route = sse_app.router.add_get('/events', sse_handler)
    status_route = sse_app.router.add_get('/status', sse_status_handler)
    
    # Add CORS to routes
    cors.add(sse_route)
    cors.add(status_route)
    
    runner = web.AppRunner(sse_app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    print(f"[SSE] HTTP Server started on http://localhost:{port}")
    print(f"[SSE] Events endpoint: http://localhost:{port}/events")
    print(f"[SSE] Status endpoint: http://localhost:{port}/status")

async def main():
    # Start background scheduler
    scheduler_thread = threading.Thread(target=cron_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="orchestration-service",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
