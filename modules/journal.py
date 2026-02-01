import os
import sys
import asyncio
from claude import Claude as Generator

# Try to import calendar modules - support both Apple and Google Calendar
try:
    import calendar_manually
    APPLE_CALENDAR_AVAILABLE = True
except (ImportError, Exception):
    APPLE_CALENDAR_AVAILABLE = False

try:
    import google_calendar
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
class Journal(object):
    def __init__(self, use_google_calendar=False):
        self.entries = []
        self.journal = ""
        self.calendar = ""
        self.use_google_calendar = use_google_calendar or os.getenv("USE_GOOGLE_CALENDAR", "").lower() == "true"

    def section_title(self):
        return "Journal Entries"


    def pull_data(self, rawmode=False):
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## calendar - Support both Google and Apple Calendar
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        calendar_data = None
        
        if self.use_google_calendar and GOOGLE_CALENDAR_AVAILABLE:
            try:
                print("Fetching Google Calendar events...")
                # Get credentials paths from environment or use defaults
                credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
                token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
                
                calendar_data = google_calendar.upcoming(credentials_file, token_file)
                print("Google Calendar data retrieved successfully")
            except Exception as e:
                print(f"Google Calendar error: {e}")
                calendar_data = None
        elif APPLE_CALENDAR_AVAILABLE:
            try:
                print("Fetching Apple Calendar events...")
                calendar_data = calendar_manually.upcoming()
                print("Apple Calendar data retrieved successfully")
            except Exception as e:
                print(f"Apple Calendar error: {e}")
                calendar_data = None
        
        # Store calendar data if available
        if calendar_data:
            self.calendar = calendar_data
        
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## obsidian
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        document = {}
        obsdir = os.getenv("OBSIDIAN_DIR", "/Users/chris/Obsidian/Geppetto/")
        
        docs = os.listdir(obsdir+"Journal/Day")
        docs.sort(reverse=True)
        docs = docs[:7]
        recent = [] 
        tasks = []
        for doc in docs[:7]:
            if doc.endswith(".md"):
                with open(obsdir+"Journal/Day/"+doc, "r") as f:
                    content = f.readlines()
                    content = content[3:]
                    recent.extend(content)
                    task_temp = [xx.strip() for xx in content if xx.strip().startswith("- [ ] ")]
                    tasks.extend(task_temp)

        for doc in docs[7:]:
            if doc.endswith(".md"):
                with open(obsdir+"Journal/Day/"+doc, "r") as f:
                    content = f.readlines()
                    task_temp = [xx.strip() for xx in content if xx.strip().startswith("- [ ] ")]
                    tasks.extend(task_temp)

        self.entries = ["# Open Tasks"] + tasks + ["# Recent Journal Entries"] + recent
        return self.entries
       
        

    def output(self):
        if not self.entries:
            return "No journal entries found."
        output = "\n".join(self.entries)
        return output
