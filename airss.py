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
from storyteller import generate_complete_newsletter
from airss_base import embed, cluster_vectors_kmeans, make_labelled_groups, make_gps, now, log

def cluster_for_narratives(arts):
    """Cluster articles to create narrative-ready groups"""
    # Embed articles for semantic similarity
    claims = [embed(aa.title + "\n" + aa.summary) for aa in arts]
    
    # Define narrative-focused tags for better story grouping
    narrative_tags = [
        # Geopolitical narratives
        'Russia Ukraine War', 'Middle East Conflict', 'US China Relations', 'European Politics',
        'Global Security', 'International Trade', 'Climate Action', 'Energy Transition',
        
        # Technology narratives  
        'AI Development', 'Tech Regulation', 'Cybersecurity', 'Social Media', 'Cryptocurrency',
        'Space Exploration', 'Electric Vehicles', 'Medical Breakthroughs',
        
        # Domestic narratives
        'US Politics', 'Economic Policy', 'Healthcare', 'Education', 'Immigration',
        'Civil Rights', 'Supreme Court', 'Elections', 'Infrastructure',
        
        # Business narratives
        'Corporate Earnings', 'Market Trends', 'Banking', 'Real Estate', 'Labor',
        'Supply Chain', 'Innovation', 'Mergers Acquisitions',
        
        # Social narratives
        'Public Health', 'Environmental Issues', 'Cultural Events', 'Sports',
        'Entertainment', 'Scientific Discovery', 'Legal Developments'
    ]
    
    vtags = np.array([embed(tag) for tag in narrative_tags])
    
    # Enhanced keyword extraction for narrative building
    for ii, xx in enumerate(claims):
        sims = vtags@xx
        use = np.argsort(sims)[::-1][:3]  # Top 3 most relevant narrative tags
        narrative_keywords = [narrative_tags[uu] for uu in use if sims[uu] >= 0.6]
        
        arts[ii].keywords = narrative_keywords
        arts[ii].vector = xx
        arts[ii].narrative_score = float(sims[use[0]]) if len(use) > 0 else 0.0
    
    # Cluster based on narrative similarity rather than just content similarity
    narrative_clusters = cluster_vectors_kmeans([xx.vector for xx in arts])
    
    # Create narrative-aware groupings
    narrative_groups = defaultdict(list)
    for ii, cluster_id in enumerate(narrative_clusters):
        # Group by primary narrative keyword + cluster
        primary_narrative = arts[ii].keywords[0] if arts[ii].keywords else "General"
        group_key = f"{primary_narrative}_{cluster_id}"
        narrative_groups[group_key].append(arts[ii])
    
    # Assign cluster IDs based on narrative groups
    cluster_map = {}
    for cluster_idx, (group_key, group_articles) in enumerate(narrative_groups.items()):
        for article in group_articles:
            article.cluster = cluster_idx
            article.narrative_group = group_key
    
    log(f"Created {len(narrative_groups)} narrative-based clusters")
    return arts

def main():
    """Main workflow with AI-driven newsletter generation"""
    today = now()
    log("Starting AIRSS newsletter generation workflow")
    
    # Fetch all articles without pre-clustering
    articles = feeds.Feeds.fetch_articles(feeds.FEEDS)
    log(f"Fetched {len(articles)} articles")
    
    # Send all articles to AI for narrative grouping and newsletter creation
    log("Generating complete newsletter from all articles...")
    html_content = generate_complete_newsletter(articles)
    log("Newsletter generation completed")
    
    # Send email
    sender = "christopherpbonnell@icloud.com"
    receiver = "christopherpbonnell@gmail.com"
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