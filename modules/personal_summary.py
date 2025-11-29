import os
try:
    from modules.wordcloud import PersonalWordCloud
except ImportError:
    from wordcloud import PersonalWordCloud

class PersonalSummary(object):
    def __init__(self):
        self.entries = []
        self.wordcloud = PersonalWordCloud()

    def pull_data(self):
        """Generate enhanced personal summary with wordcloud"""
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## calendar - simplified for now
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        self.entries = ["#Calendar", "{\"Mine\": {}, \"Family\": {}}"]

        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        ## obsidian
        ## =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
        obsdir = "/Users/chris/Obsidian/Geppetto/"

        docs = os.listdir(obsdir+"Journal/Day")
        docs.sort(reverse=True)
        docs = docs[:7]
        recent = []
        tasks = []
        all_content = []  # For wordcloud generation

        for doc in docs[:7]:
            if doc.endswith(".md"):
                with open(obsdir+"Journal/Day/"+doc, "r") as f:
                    content = f.readlines()
                    content = content[3:]  # Skip header
                    recent.extend(content)
                    all_content.extend(content)
                    task_temp = [xx.strip() for xx in content if xx.strip().startswith("- [ ] ")]
                    tasks.extend(task_temp)
 
        for doc in docs[7:]:
            if doc.endswith(".md"):
                with open(obsdir+"Journal/Day/"+doc, "r") as f:
                    content = f.readlines()
                    all_content.extend(content)
                    task_temp = [xx.split("- [ ] ")[-1].strip() for xx in content if xx.strip().startswith("- [ ] ")]
                    tasks.extend(task_temp)

        # Generate the basic text summary
        #basic_summary = ["# Open Tasks"] + tasks #+ ["# Recent Journal Entries"] + recent

        # Create wordcloud from all content
        all_text = "\n".join(all_content + tasks)
        return "\n\n".join(tasks)
        #wordcloud_svg = self.wordcloud.create_wordcloud_svg(all_text, width=500, height=200, max_words=20)
        #stats = self.wordcloud.create_summary_stats(all_text)
        #return stats
        # Enhanced HTML output
        enhanced_summary = f"""
<div style='font-family:sans-serif;'>
{stats}

<div style='margin-top: 30px;'>
<h4>Current Tasks ({len(tasks)} items)</h4>
<ul style='font-size: 14px; line-height: 1.6;'>
{"".join([f"<li>{task[6:]}</li>" for task in tasks[:10]])}
{"<li><em>...and more</em></li>" if len(tasks) > 10 else ""}
</ul>
</div>

<div style='margin-top: 20px;'>
<h4>Recent Themes</h4>
<div style='font-size: 13px; line-height: 1.5; color: #555; max-height: 200px; overflow-y: auto;'>
{"<br/>".join([line.strip() for line in recent[:15] if line.strip() and not line.strip().startswith("-")])}
</div>
</div>
</div>
"""

        # Return both formats
        return enhanced_summary

if __name__ == "__main__":
    summary = PersonalSummary()
    result = summary.pull_data()
    print("Enhanced format:")
    print(result["enhanced"])
    print("\n" + "="*50 + "\n")
    print("Raw format:")
    print(result["raw"][:500] + "...")