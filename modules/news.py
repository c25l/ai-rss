from claude import Claude as Generator
import feedbiz
class News(object):
    def __init__(self):
        self.articles = []
        self.research = []
        
    def section_title(self):
        return "News Articles"
    
    def pull_data(self):
        self.articles = {xx:feedbiz.feedbiz(xx,blacklist=["Trump"]) for xx in ["news","culture","ai","local"]}

    def output(self):
        if not self.articles:
            return "No news articles found."
        prompt = """

Generate news intelligence brief from RSS sources.

You will be given several news sources in several sections. Your job is to synthesize these into a coherent narrative, focusing on major stories, cultural developments, AI/tech news, and local Longmont updates.

### Content Guidelines:
- Filter out anything to do with Trump, Israel sports, music, performances
- Synthesize articles into coherent narrative sections
- Create engaging headlines connecting related articles
- Use markdown with inline links: [article title](url)

### Output Requirements:
```markdown
## News Intelligence Brief

### US & World News
[Synthesized narrative of major stories]

### Cultural & Society
[Interesting cultural developments and discussions]

### AI & Technology
[Relevant AI/tech developments]

### Local Longmont
[Local news and community updates]
```
Please return the document in markdown as output.
"""
        output=[]
        for xx,yy in self.articles.items():
            if not yy:
                continue
            try:
                text = prompt + "\n\n## " + xx +'\n'.join(yy).replace('"', '').replace("'", "")
                temp = Generator().generate(text)
                if not temp or temp.strip().startswith("Execution error"):
                    raise Exception("No output from Claude", temp, text)
                output.append("## "+xx)
                output.append(temp)
            except Exception as e:
                print("Error generating news output:", e)
                output.append("## "+xx+ "\n".join(yy))
        return "\n".join(output)
