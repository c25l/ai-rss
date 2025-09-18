#!/usr/bin/env  /Users/chris/source/airss/venv/bin/python3
import claude
import outbox
import json
import datetime
from modules import journal, news, research, weather, spaceweather, personal_summary, wordcloud


def main():
    wtr = weather.Weather().pull_data()
    swr = spaceweather.SpaceWeather().pull_data()
    rsch = research.Research().pull_data()
    nws = news.News().pull_data()
    pers = personal_summary.PersonalSummary().pull_data()
    jrl = journal.Journal().pull_data()
    out = [str(wtr),str(swr)]

    for xx in [nws, pers, jrl,rsch]:
        out.append("\n\n---\n\n")
        out.append(wordcloud.PersonalWordCloud().create_wordcloud_svg(str(xx)))

    ## so we're going to try embeddinggemma to pull these things into their groups here, and then group them together.
    ## this is a divide-and-conquer first grouping, so we will go fast. 
    personal = ["US & World News",
    "Cultural & Society",
    "AI & Technology",
    "Local Longmont",
    ]

    outbox.send_email("<br>".join(out), subject=f"📰 {datetime.datetime.now().strftime('%Y-%m-%d')}")

    personal = """
    ## Personal Status Update
    ### This Week's Key Items
    ### Upcoming Week
    ### Action Items
    ### Recent Activity
    """
    #research=    
    Bad = ["System designs without scalability analysis",
    "Missing resource utilization metrics or cost analysis",
    "Theoretical models disconnected from operational constraints",
    "Benchmarks on toy problems rather than production scale"]
    good = [
    "Provide quantitative performance analysis with statistical rigor",
    "Address real bottlenecks in distributed systems",
    "Include failure mode analysis and reliability considerations",
    "Connect algorithmic choices to hardware/infrastructure implications"]

    prefs = ["distributed training and inference systems",
    "GPU memory management and optimization",
    "model serving and deployment infrastructure",
    "workload characterization and resource allocation",
    "performance modeling for ML systems"]

    interest = ["system-level optimizations for transformer inference",
    "distributed computing patterns for large model training",
    "hardware-software co-design for ML workloads",
    "operational aspects of ML infrastructure at scale"]

    disinterest =[
    "pure algorithmic improvements without system implications",
    "single-GPU optimizations",
    "theoretical complexity without practical validation",
    "AGI, robotics, biology applications"]

    opt = """
    ### Top Papers (Analyzed [X] of [Y] total papers)
    [Best 5 papers with abstracts and analysis]
    ```
    """
    finalize = """
    ## Final Step: Send the accumulated document
    Once you have finished all the subtasks, send the finalized document via `mcp__utilities__outbox_flush`

    """



if __name__ == "__main__":
    main()
