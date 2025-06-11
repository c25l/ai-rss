#!/usr/bin/env python3
"""
Custom Newsletter Generator
Creates and sends AI-generated newsletter via AIRSS email system
"""

import smtplib
from email.message import EmailMessage
from datetime import datetime
import feeds
from storyteller import generate_complete_newsletter

def create_newsletter_content():
    """Create AI-generated newsletter HTML content using RSS feeds"""
    
    # Fetch current articles from RSS feeds
    articles = feeds.Feeds.fetch_articles(feeds.FEEDS)
    print(f"Fetched {len(articles)} articles for newsletter generation")
    
    # Generate newsletter using AI
    html_content = generate_complete_newsletter(articles)
    
    return html_content

def send_newsletter():
    """Send the newsletter using AIRSS email configuration"""
    
    # Create newsletter content
    html_content = create_newsletter_content()
    
    # Email configuration (from airss.py)
    sender = "christopherpbonnell@icloud.com"
    receiver = "christopherpbonnell@gmail.com" 
    password = "vqxh-oqrp-wjln-eagl"

    # Create email message
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"Daily News Digest - {datetime.now().strftime('%B %d, %Y')}"
    msg.set_content(html_content, subtype="html")
    
    try:
        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(msg['From'], password)
            server.send_message(msg)
        print("✅ Newsletter sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

if __name__ == "__main__":
    print("📰 Creating comprehensive newsletter...")
    success = send_newsletter()
    if success:
        print("🎉 Daily News Digest delivered!")
    else:
        print("💥 Newsletter delivery failed!")