#!/usr/bin/env python
"""
Agent-Centric Daily Workflow

This is the new architectural approach where the LLM agent has full autonomy
to decide content importance and presentation structure.

Unlike daily_workflow.py (constrained-LLM approach with hard-coded sections),
this gives the agent tools and sources, then lets it decide everything else.
"""

import datetime
import hashlib
import json
import sys
import os
import dotenv
from agent_briefing import AgentBriefing
from emailer import Emailer

BRIEFING_ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefings")


def _hash_preferences_file():
    """Return a short SHA-256 hex digest of preferences.yaml (or 'default' if absent)."""
    pref_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preferences.yaml")
    if os.path.exists(pref_path):
        with open(pref_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    return "default"


def _find_cached_briefing(today_short, prefs_hash):
    """Look for a briefing JSON from today with matching preferences hash."""
    os.makedirs(BRIEFING_ARCHIVE_DIR, exist_ok=True)
    path = os.path.join(BRIEFING_ARCHIVE_DIR, f"{today_short}-{prefs_hash}.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f), path
        except (json.JSONDecodeError, OSError):
            pass
    return None, None


def main():
    """
    Generate and send daily briefing using agent-centric approach.
    """
    # Load environment - use .env from current directory or specify via ENV_FILE
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    
    # Change to working directory if specified
    work_dir = os.getenv("WORK_DIR")
    if work_dir and os.path.exists(work_dir):
        os.chdir(work_dir)
    
    print("="*80)
    print("AGENT-CENTRIC DAILY BRIEFING")
    print("="*80)
    print()
    
    # Create agent briefing system
    briefing_system = AgentBriefing()
    
    # Get email preferences
    email_prefs = briefing_system.preferences.get('email_preferences', {})
    include_weather = email_prefs.get('include_weather', True)
    include_astronomy = email_prefs.get('include_astronomy', True)
    include_stocks = email_prefs.get('include_stocks', False)
    subject_format = email_prefs.get('subject_format', "Agent-Driven H3LPeR Briefing - {date}")
    
    # Hash preferences for cache lookup
    prefs_hash = _hash_preferences_file()
    today_short = datetime.datetime.now().strftime("%y%m%d")
    print(f"Preferences hash: {prefs_hash}")
    
    # Check for a cached briefing from today with same preferences
    briefing_doc, cached_path = _find_cached_briefing(today_short, prefs_hash)
    
    if briefing_doc is not None:
        print(f"✓ Found cached briefing: {cached_path}")
        print("  Skipping generation, sending cached version.")
    else:
        # Generate briefing
        try:
            print("Generating agent-driven briefing (structured JSON)...")
            briefing_doc = briefing_system.generate_briefing(
                days=1,
                include_weather=include_weather,
                include_stocks=include_stocks,
                include_astronomy=include_astronomy,
                use_enhanced_prompting=True
            )
            
            # Stamp the preferences hash into the document
            briefing_doc["preferences_hash"] = prefs_hash
            
            print("\n✓ Briefing generated and validated successfully")
            
        except Exception as e:
            print(f"\n✗ Error generating briefing: {e}")
            sys.exit(1)
        
        # Archive the JSON briefing
        try:
            os.makedirs(BRIEFING_ARCHIVE_DIR, exist_ok=True)
            archive_name = f"{today_short}-{prefs_hash}.json"
            archive_path = os.path.join(BRIEFING_ARCHIVE_DIR, archive_name)
            with open(archive_path, "w") as f:
                json.dump(briefing_doc, f, indent=2, default=str)
            print(f"✓ Briefing archived to {archive_path}")
        except Exception as e:
            print(f"Warning: Could not archive briefing: {e}")
    
    # Send email (if enabled in preferences)
    send_email = email_prefs.get('send_email', False)
    if send_email:
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            subject = subject_format.format(date=today)

            emailer = Emailer()
            emailer.send_email_json(briefing_doc, subject=subject)

            print(f"✓ Agent briefing emailed successfully")

        except Exception as e:
            print(f"\n✗ ERROR: Failed to send email: {e}")
            sys.exit(1)
    else:
        print("✓ Email sending disabled")
    
    # Run citation analysis (always run to keep data fresh)
    try:
        from citations_data import generate_and_save_citations
        print("\nRunning citation analysis on research papers...")
        # Reuse articles already fetched during briefing generation
        research_articles = getattr(briefing_system, 'all_research_articles', None)
        if research_articles:
            print(f"  Reusing {len(research_articles)} pre-fetched research articles")
        citation_data = generate_and_save_citations(days=1, top_n=50, min_citations=1, articles=research_articles)
        if citation_data:
            print(f"✓ Citation analysis complete: {citation_data['paper_count']} papers")
        else:
            print("⚠ Citation analysis had no results")
    except Exception as e:
        print(f"⚠ Citation analysis error: {e}")
    
    # Publish to static site (opt-in via preferences or PAGES_DIR env var)
    publish_enabled = email_prefs.get('publish_site', False)
    site_dir = os.environ.get("PAGES_DIR") or os.environ.get("GITHUB_PAGES_DIR")
    if publish_enabled or site_dir:
        try:
            from publish_site import publish_briefing
            if publish_briefing(site_dir=site_dir):
                print("✓ Static site published")
            else:
                print("⚠ Static site publish skipped or failed")
        except Exception as e:
            print(f"⚠ Static site publish error: {e}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
