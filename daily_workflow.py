#!/usr/bin/env /Users/chris/source/airss/venv/bin/python3
import claude
import outbox
import feeds
import datetime
import requests
from bs4 import BeautifulSoup
from modules import personal_summary, research, weather, spaceweather
def main():
    articles = []
    sources = ["https://rss.nytimes.com/services/xml/rss/nyt/US.xml", 
               "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
               "https://www.theatlantic.com/feed/all/", 
               "https://heathercoxrichardson.substack.com/feed", 
               "https://rss.metafilter.com/metafilter.rss",
                 "https://acoup.blog/feed/",
                 "https://www.microsoft.com/en-us/research/feed/",
                   "https://www.nature.com/nature.rss", 
                   "https://www.daemonology.net/hn-daily/index.rss",
                   "https://blog.google/technology/ai/rss/", 
                   "https://www.longmontleader.com/rss/",
                     "https://www.reddit.com/r/Longmont.rss"]
    for src in sources:
        articles.extend([xx.out_rich() for xx in feeds.Feeds.get_articles(src)])
    now=datetime.datetime.now()
    text=BeautifulSoup(requests.get(f"https://tldr.tech/ai/{now:%Y-%m-%d}").text, "html.parser")
    text=text.find_all("article")
    articles.extend([str(xx) for xx in text])
    text=BeautifulSoup(requests.get(f"https://www.daemonology.net/hn-daily/{now-datetime.timedelta(days=1):%Y-%m-%d}.html").text, "html.parser")
    text= text.find_all("span", class_="storylink")
    articles.extend([str(xx) for xx in text])
    text=BeautifulSoup(requests.get(f"https://en.wikipedia.org/Main_Page").text, "html.parser")
    text= text.find_all("div", id_="mp_itr")
    articles.extend([str(xx) for xx in text])
    # prompt="/utilities:Daily_Workflow (MCP)"
    # claude.Claude().generate(prompt)
    preprompt="""
        Please be concise and to the point in your summaries. 
        Do not introduce or conclude, do not summarize the work done unless specifically asked to.
    """
# Subtask 1: Generate news intelligence brief from RSS sources.
    weather_prompt=""" 
# Output Requirements:
- Weather
    - Based on utilities mcp weather tool
        - Please summarize the given html weather forecast concisely using emojis and symbols and numbers format.
        - I only want the weather for the next 3 days.
-Space Weather
    - Based on utilities mcp space_weather tool
        - Please analyze the given data to provide a concise summary of the current and upcoming space weather conditions.
        - Include any significant geomagnetic activity or solar events that may impact Earth.
        - Please use emojis and symbols but do not express completel thoughts, only data.

# Begin data
        """
    ppt = preprompt+weather_prompt+weather.Weather().pull_data()+"\n\n"+spaceweather.SpaceWeather().pull_data()
    out1 = claude.Claude().generate(ppt)
    outbox.add(out1, "🌤️ Daily Weather and Space Weather Summary")
    print(out1)

    news_prompt="""
Your job is to generate a news briefing. 
There must be inline markdown links `[article title](url)` to the original sources for these articles.
- News Intelligence Brief
    - At most 7 total stories -- articles may be combined into larger themes if needed
    - Please make these stories of interest if there are articles to substantiate them:
        - Epstein files
        - AI model developments
        - AI hardware developments
        - AI datacenter developments
        - Local Longmoont news
        - Astromony / Space news
- please return the output document.

# Begin news:
"""
    print("\n\n".join(articles))
    out2 = claude.Claude().generate(preprompt+news_prompt+ "\n\n".join(articles))
    print(out2)
    outbox.add(out2, "📰 Daily News Intelligence Brief")
#- Please deliver the finished markdown document via `utilities mcp outbox_add_document` 
#- Do not flush the outbox yourself, just add the document.
# Subtask 2: Personal Summary

    personal="""
output a personal status update based on: 
- what projects have I been working on lately?

Begin dataset:    
"""
    out3 = claude.Claude().generate(preprompt+personal+personal_summary.PersonalSummary().pull_data())
    print(out3)
    outbox.add(out3, "🗒️ Personal Summary Update")

    research_prompt = """
I want at most 5 preprints, focusing on practical real world developments in 
    - training or inference of ai models at scale.
    - especially including design of infrastructure and new hardware
please return the document
Please make sure to include inline markdown links `[article title](url)` to the original sources for these articles.

# Begin research articles:

"""
    rsch=feeds.Feeds.get_articles("https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR")
    rsch = "\n\n".join([xx.out_rich() for xx in rsch])
    if len(rsch.split("\n"))<3:
        rsch="No new research articles found."
        out4 = claude.Claude().generate(preprompt+research_prompt+rsch)
    
        outbox.add(out4, "📚 Research Preprints Summary")
    outbox.send_all()

if __name__ == "__main__":
    main()
