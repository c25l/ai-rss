import numpy as np
import subprocess
import psycopg2
from claude import Claude as Generator
import feedbiz
import requests
from random import shuffle

class Research:
    articles = []
    def __init__(self):
        self.articles = []

    def section_title(self):
        return "Arxiv Review"
   
    def pull_data(self):
        self.articles = feedbiz.feedbiz("research", whitelist=["Announce Type: new"])
        if self.articles == []:
            return ""
        outputs = []
        total = sum([len(xx) for xx in self.articles])
        if total < 25000:
            return "## Research articles\n\n" + "\n\n".join(self.articles)
        
        shuffle(self.articles)
        running_total = 22
        outputs.append("## Research articles\ns")
        for xx in self.articles:
            running_total += len(xx)+2
            if running_total>=25000:
                break
            outputs.append(xx)
        return "\n\n".join(outputs)
    
if __name__ == "__main__":
    print("loading object")
    xx = Research()
    print("pulling data")
    xx.pull_data()

