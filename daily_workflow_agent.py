#!/usr/bin/env python
"""
Agent-Centric Daily Workflow

This is the new architectural approach where the LLM agent has full autonomy
to decide content importance and presentation structure.

Unlike daily_workflow.py (constrained-LLM approach with hard-coded sections),
this gives the agent tools and sources, then lets it decide everything else.
"""

import datetime
import sys
import os
import dotenv
from agent_briefing import AgentBriefing
from emailer import Emailer


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
    print("This workflow gives the AI agent full autonomy to:")
    print("  • Decide which content matters")
    print("  • Structure the briefing dynamically")
    print("  • Synthesize and connect information")
    print("  • Create its own narrative flow")
    print()
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
    
    # Generate briefing with full agent autonomy and enhanced multi-step prompting
    try:
        print("Generating agent-driven briefing with multi-step reasoning...")
        briefing_content = briefing_system.generate_briefing(
            days=1,
            include_weather=include_weather,
            include_stocks=include_stocks,
            include_astronomy=include_astronomy,
            use_enhanced_prompting=True  # Use multi-step reasoning with example format
        )
        
        print("\n✓ Briefing generated successfully")
        
    except Exception as e:
        print(f"\n✗ Error generating briefing: {e}")
        sys.exit(1)
    
    # Send email
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        subject = subject_format.format(date=today)
        
        # Send briefing directly without preamble
        emailer = Emailer()
        emailer.send_email(briefing_content, subject=subject)
        
        print(f"✓ Agent briefing emailed successfully")
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to send email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
