import os
# import calendar_manually  # Commented out - macOS specific, not used
import asyncio
from claude import Claude as Generator
class Journal(object):
    def __init__(self):
        self.entries = []
        self.journal = ""
        self.calendar = ""

    def section_title(self):
        return "Journal Entries"


    def pull_data(self, rawmode=False):
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## calendar
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        # try:
        #     print("calendar")
        #     document = {}
        #     cals = calendar_manually.upcoming()
        #     document["#Calendar"] = cals
        #     self.entries = document
        # except Exception as e:
        #     print("calendar bad", e)
        #     self.entries["State"] = "Calendar system failure."
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## obsidian
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        document = {}
        obsdir = os.getenv("OBSIDIAN_DIR", "/Users/chris/Obsidian/Geppetto/")
        journal_dir = obsdir + "Journal/Day"

        # Check if journal directory exists
        if not os.path.exists(journal_dir):
            print(f"Journal directory not found: {journal_dir}")
            self.entries = []
            return self.entries

        docs = os.listdir(journal_dir)
        docs.sort(reverse=True)
        docs = docs[:7]
        recent = []
        tasks = []
        for doc in docs[:7]:
            if doc.endswith(".md"):
                with open(journal_dir+"/"+doc, "r") as f:
                    content = f.readlines()
                    content = content[3:]
                    recent.extend(content)
                    task_temp = [xx.strip() for xx in content if xx.strip().startswith("- [ ] ")]
                    tasks.extend(task_temp)

        for doc in docs[7:]:
            if doc.endswith(".md"):
                with open(journal_dir+"/"+doc, "r") as f:
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
