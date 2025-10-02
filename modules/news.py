from claude import Claude as Generator
import feedbiz
class News(object):
    def __init__(self):
        self.articles = []
        self.research = []
        
    def section_title(self):
        return "News Articles"
    
    def pull_data(self):
        self.articles = {xx:feedbiz.feedbiz(xx,blacklist=["Trump","Israel","Musk","Gaza","Broncos"]) for xx in ["news","culture","ai","local"]}
        return "\n\n".join([f"## {xx} \n\n {'\n\n'.join(self.articles[xx])}" for xx in self.articles])
