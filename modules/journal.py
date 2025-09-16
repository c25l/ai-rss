import os
import calendar_manually
import asyncio
from claude import Claude as Generator
class Journal(object):
    def __init__(self):
        self.entries = []
        self.journal = ""
        self.calendar = ""

    def section_title(self):
        return "Journal Entries"


    def pull_data(self):
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## calendar
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        try:
            print("calendar")
            document = []
            cals = calendar_manually.upcoming()
            document.append("#Calendar")
            document.append(cals)           
            self.entries = document
        except Exception as e:
            print("calendar bad", e)
            self.entries.append("Calendar system failure.")
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## obsidian
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=            
        document = []
        obsdir ="/Users/chris/Obsidian/Geppetto/"
        
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

        self.entries += ["# Open Tasks"] + tasks + ["# Recent Journal Entries"] + recent
        return "\n".join(self.entries)
        

    def output(self):
        if not self.entries:
            return "No journal entries found."
        output = "\n".join(self.entries)
        prompt ="""
## Task 1: Personal Summary

Add a personal status update by gathering information from multiple sources.

You will be given calendar events, recent Obsidian materials, and open todos. Your job is to synthesize this into a coherent personal status update.


### Output Requirements:
- Review materials and integrate into a factual status briefing
- Focus on items needing attention, follow-up, or preparation

```markdown
## Personal Status Update

### This Week's Key Items
[Today's important items]

### Upcoming Week
[Next week's notable events and commitments]

### Action Items
[Open todos and items requiring attention]

### Recent Activity
[Relevant Obsidian materials from past week]
```
Return this document to be used in the aggregated daily brief."""
        try:
            temp = Generator().generate("\n".join([prompt,"\n---\n",output]))

            if not temp:
                raise Exception("No output from Claude")
            return temp
        except Exception as e:
            print("Error generating research output:", e)
            return output
