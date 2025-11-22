import feedbiz
class News(object):
    def __init__(self):
        self.articles = []
        self.research = []
        
    def section_title(self):
        return "News Articles"
    
    def pull_data(self):
        self.articles = {xx:feedbiz.feedbiz(xx,blacklist=["Trump","Israel","Musk","Gaza","Broncos"]) for xx in ["news","culture","ai","local"]}
        # Consolidate all stories into a single section
        all_stories = []
        for category in self.articles:
            all_stories.extend(self.articles[category])
        return f"## Stories\n\n{chr(10).join(all_stories)}"
