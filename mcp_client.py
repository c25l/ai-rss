from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import json
from datetime import datetime, timedelta, timezone
import subprocess
import markdown
import smtplib
from email.message import EmailMessage
### the model could do all of this, but the point here is to ensure that no models are called unless there's some reason to.

server_params = StdioServerParameters(
    command = '/opt/homebrew/bin/npx',  # Path to mcp-ical server executable
    args = ["@cocal/google-calendar-mcp"],  # Path to mcp-ical server
    cwd = '/Users/chris/source/airss',  # Set working directory
    env = {"GOOGLE_OAUTH_CREDENTIALS":"/Users/chris/source/airss/credentials.json"}  # Path to Google OAuth credentials
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write,
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            #tools = await session.list_tools()

            # Get current time and round down to nearest half hour
            time = datetime.now()
            time = time - timedelta(minutes=time.minute%30, seconds=time.second, microseconds=time.microsecond)
            endtime = time + timedelta(minutes=30)
            print("checking calendar for events between", time, "and", endtime)
            
            # Call mcp-ical list_events tool
            events = await session.call_tool("list-events", arguments={
                "timeMin": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeMax": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "America/Denver",
                "calendarId":"969a157ef1848f6ff639e8099d8ecd9b6b07f6c0f7f7d781b5c09e9ff8e738b8@group.calendar.google.com"
            })
            
            events_text = events.model_dump()['content'][0]['text']
            if "No events found" not in events_text and events_text.strip():
                print("Found events:")
                print(events_text)
                
                # Extract event descriptions from the mcp-ical format
                # Look for events with "Notes: " containing substantial content
                lines = events_text.split('\n')
                current_event = {}
                events_to_process = []
                current_event = {'title': lines[0].replace('Event: ', '').strip().rstrip(',')}
                notes_loc = events_text.find('Description:')
                current_event['notes'] = events_text[notes_loc:].replace('Description: ', '').strip()
                print(current_event)
                if current_event.get('notes') and len(current_event['notes']) > 100:
                    events_to_process.append(current_event)
                
                if not events_to_process:
                    print("No events with substantial descriptions found.")
                    return
                
                for event in events_to_process:
                    print(f"Processing Event: {event['title']}")
                    print(f"Description length: {len(event['notes'])} chars")
                    
                    # Execute Claude CLI with the event description
                    result = subprocess.run([
                        "claude", "--dangerously-skip-permissions", "-p", 
                        event['notes'].replace('"', '\\"').replace("'", "\\'")
                    ], capture_output=True, text=True)
                    
                    # Log both stdout and stderr
                    with open("logs/out.log", "a") as f: 
                        if result.stdout:
                            f.write(f"\n=== {event['title']} - {datetime.now().isoformat()} ===\n")
                            f.write(result.stdout)
                            f.write("\n")
                    
                    with open("logs/err.log", "a") as f: 
                        if result.stderr:
                            f.write(f"\n=== {event['title']} - {datetime.now().isoformat()} ===\n")
                            f.write(result.stderr)
                            f.write("\n")
                    
                    # Print stdout to console as well
                    if result.stdout:
                        print("Claude output:")
                        print(result.stdout)
                    
            else:
                print("No events found in the specified time range.")


# Old parsing functions removed - no longer needed with mcp-ical format


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
