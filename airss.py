#!/usr/bin/env python3
"""
AIRSS with Story Generation
Alternative main script that generates news stories instead of simple article lists
"""

from collections import defaultdict
from datetime import datetime
import numpy as np
from datamodel import Article,Group
import feeds 
import smtplib
from email.message import EmailMessage
from storyteller import generate_newsletter_from_group_objects
from airss_base import embed, cluster_vectors_kmeans, make_labelled_groups, make_gps, now, log, cluster


def main():
    """Main workflow with AI-driven newsletter generation"""
    today = now()
    log("Starting AIRSS newsletter generation workflow")
    
    # Fetch and cluster articles
    articles = feeds.Feeds.fetch_articles(feeds.FEEDS)
    log(f"Fetched {len(articles)} articles")
    
    # Use the base clustering system (same as original airss.py)
    articles = cluster(articles)
    
    # Create groups from clusters
    cluster_groups = defaultdict(list)
    cluster_cts = defaultdict(int)
    for article in articles:
        cluster_cts[article.cluster] += 1
        cluster_groups[article.cluster].append(article)

    ccts2 = defaultdict(int)
    for ii,xx in cluster_cts.items():
        ccts2[xx] += 1            
    print(ccts2)
    # Convert to labeled Group objects
    gps = make_labelled_groups(cluster_groups)
    
    # Generate newsletter from Group objects (new individual processing approach)
    log("Generating newsletter from clustered groups...")
    html_content = generate_newsletter_from_group_objects(gps)
    log("Newsletter generation completed")
    
    # Send email
    sender = "christopherpbonnell@icloud.com"
    receiver = "christopherpbonnell+airss@gmail.com"
    password = "vqxh-oqrp-wjln-eagl"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"📰 News Intelligence Brief - {datetime.now().strftime('%Y-%m-%d')}"
    msg.set_content(html_content, subtype="html")
    
    try:
        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(msg['From'], password)
            server.send_message(msg)
        log("Email sent successfully")
    except Exception as e:
        log(f"Email sending failed: {e}")

if __name__ == "__main__":
    main()