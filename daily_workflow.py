#!/usr/bin/env python3
import env_loader  # Load environment variables first
import claude
import feeds
import datetime
import requests
from bs4 import BeautifulSoup
from modules import journal, research, weather, spaceweather, emailer
from datamodel import Article
def main():
    articles = []
    content_sections = []
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
        articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=3)])
    now=datetime.datetime.now()
    text=BeautifulSoup(requests.get(f"https://tldr.tech/ai/{now:%Y-%m-%d}").text, "html.parser")
    text=text.find_all("article")
    articles.extend([Article(title=str(xx),summary="", published_at=now,source="tldr.tech/ai") for xx in text])
    text=BeautifulSoup(requests.get(f"https://www.daemonology.net/hn-daily/{now-datetime.timedelta(days=1):%Y-%m-%d}.html").text, "html.parser")
    text= text.find_all("span", class_="storylink")
    articles.extend([Article(title=str(xx), published_at=now, source="hacker news daily",summary="")  for xx in text])
    
    preprompt="""
        Please be concise and to the point in your summaries.
        Do not introduce or conclude, do not summarize the work done unless specifically asked to.
    """
# Subtask 1: Generate weather and space weather summaries (deterministic)
    weather_forecast = weather.Weather().format_forecast()
    spaceweather_forecast = spaceweather.SpaceWeather().format_forecast()

    out1 = f"## Weather Forecast\n\n{weather_forecast}\n\n## Space Weather\n\n{spaceweather_forecast}"
    content_sections.append(f"# 🌤️ Daily Weather and Space Weather Summary\n\n{out1}")
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
    # Format articles for Claude
    articles_text = "\n\n".join([article.out_rich() for article in articles])
    out2 = claude.Claude().generate(preprompt + news_prompt + articles_text)
    print(out2)
    content_sections.append(f"# 📰 Daily News Intelligence Brief\n\n{out2}")
#- Please deliver the finished markdown document via `utilities mcp outbox_add_document` 
#- Do not flush the outbox yourself, just add the document.
# Subtask 2: Personal Summary

    j = journal.Journal()
    j.pull_data()
    personal = j.output()
    breakpt = [ii for ii,xx in enumerate(personal.split("\n")) if xx.strip().startswith("# Recent Journal Entries")]
    breakpt = breakpt[0] if breakpt else 0
    print(personal)
    todos = "\n".join(personal.split("\n")[:breakpt])
    personal = "\n".join(personal.split("\n")[breakpt:])
    output = claude.Claude().generate(preprompt+"""What follows are s series of my personal journal entries and open tasks. Please summarize these concisely to answer the question of "what am I up to lately?" and "what do i need to worry about?"
# \n\n""" + personal) 
    content_sections.append(f"# 🗒️ Personal Summary Update\n\n{todos}\n{output}")

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
    print("RSCJ:",len(rsch),len(rsch.split("\n")),rsch)
    if len(rsch.strip().split("\n"))<3:
        rsch="No new research articles found."
    else:
        out4 = claude.Claude().generate(preprompt+research_prompt+rsch)
        content_sections.append(f"# 📚 Research Preprints Summary\n\n{out4}")

    # Send all accumulated content via emailer
    final_content = "\n\n---\n\n".join(content_sections)
    emailer.send_email(final_content)

if __name__ == "__main__":
    main()
