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
    command = 'node',
    args = ['build/index.js'],  # Path to your server script
    cwd = 'google-calendar-mcp',  # Set the working directory to google-calendar-mcp
    env = None
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write,
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()

            # Call a tool
            time = await session.call_tool("get-current-time", arguments = {})
            time = datetime.fromisoformat(json.loads(time.model_dump()['content'][0]['text'])['currentTime']['utc'])
            time = time - timedelta(minutes=time.minute%30, seconds=time.second,microseconds=time.microsecond)   # Round down to the nearest half hour
            endtime = time + timedelta(minutes=30)
            print("checking calendar for events between", time, "and", endtime )
            events = await session.call_tool("list-events", arguments={"calendarId": '969a157ef1848f6ff639e8099d8ecd9b6b07f6c0f7f7d781b5c09e9ff8e738b8@group.calendar.google.com',
                                                                       "timeMin": str(time.isoformat().split(".")[0]),
                                                                       "timeMax": str(endtime.isoformat().split(".")[0])})# calendar})
            if "No events found" not in str(events):
                events = parse(events.model_dump()['content'][0]['text'])
                print(events)
                events = [xx for xx in events if  'Start' in xx and (xx['Start'] >= time.replace(tzinfo=None) and xx['Start'] <= endtime.replace(tzinfo=None))]
                if len(events)==0:
                    print("No events remained in the specified time range.")
                    return
                for zz in events:
                    if "Event" in zz:
                        print(f"Event: {zz['Event']}")
                    else:
                        print(f"Event: {zz['Description'][:200]}")
                    result = subprocess.run(["claude", "--dangerously-skip-permissions", "-p", zz["Description"].replace('"', '\\"').replace("'", "\\'")],capture_output=True, text=True)

                    with open("logs/err.log","a") as f: 
                        f.writelines(result.stderr.strip())
            else:
                print("No events found in the specified time range.")


def timeparse(timetext):
    dt = datetime.strptime(timetext, "%a, %b %d, %Y, %I:%M %p %Z")
    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def parse(text):
    texts = text.split("\n")
    outout = []
    for ii in range(1,int(texts[0].split(" ")[1])+1):
        start = [ll for ll,yy in enumerate(texts) if  yy.startswith(f"{ii}. Event:")]
        end = [ll for ll,yy in enumerate(texts) if  yy.startswith(f"{ii+1}. Event:")]
        if len(start)==0:
            continue
        start = start[-1]
        if len(end)==0:
            end = len(texts)
        print(start,end)
        outout.append(parse_inner(texts[start:end]))
    return outout

def parse_inner(thistask):
    out= {}
    if len(thistask) < 4:
        print("Skipping task with insufficient information:", thistask)
        return out
    out["Event"] = thistask[0].split("Event:")[-1]
    out["Event ID"] = thistask[1].split("Event ID:")[-1]
    startline = [ii for ii, yy in enumerate(thistask) if yy.startswith("Start:")]
    if len(startline)==0:
        print("No start line found in task:", thistask)
        return {}
    startline = startline[0]
    out["Description"]= "\n".join(thistask[2:startline])
    out["Start"] = timeparse(thistask[startline].split("Start:")[-1].strip())
    out["End"] = timeparse(thistask[startline+1].split("End:")[-1].strip())
    return out


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
