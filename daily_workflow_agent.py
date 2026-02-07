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
    
    # Generate briefing with full agent autonomy
    try:
        print("Generating agent-driven briefing...")
        briefing_content = briefing_system.generate_briefing(
            days=1,
            include_weather=True,
            include_stocks=True,
            include_astronomy=True
        )
        
        print("\n✓ Briefing generated successfully")
        
    except Exception as e:
        print(f"\n✗ Error generating briefing: {e}")
        sys.exit(1)
    
    # Send email
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        subject = f"Agent-Driven H3lPeR Briefing - {today}"
        
        # Add header explaining the new approach
        header = """# Agent-Driven Daily Briefing

*This briefing was autonomously structured by an AI agent with full editorial freedom.*

---

"""
        final_content = header + briefing_content
        
        emailer = Emailer()
        emailer.send_email(final_content, subject=subject)
        
        print(f"✓ Agent briefing emailed successfully")
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to send email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
