#!/usr/bin/env python
"""
Demo script to showcase the agent-centric architecture.

This demonstrates the key difference: the agent has full autonomy
to decide what matters and how to present it.
"""

import datetime
from agent_briefing import AgentBriefing


def demo_basic_briefing():
    """Demo 1: Basic agent-driven briefing"""
    print("\n" + "="*80)
    print("DEMO 1: Basic Agent-Driven Briefing")
    print("="*80)
    print("\nThe agent will:")
    print("  • Fetch content from all configured sources")
    print("  • Autonomously decide what's important")
    print("  • Structure the briefing however it thinks best")
    print("  • Add synthesis and connections\n")
    
    briefing = AgentBriefing()
    result = briefing.generate_briefing(days=1)
    
    print("\n--- AGENT OUTPUT START ---\n")
    print(result)
    print("\n--- AGENT OUTPUT END ---\n")
    
    return result


def demo_focused_briefing():
    """Demo 2: Focused briefing on specific topics"""
    print("\n" + "="*80)
    print("DEMO 2: Focused Briefing on Specific Topics")
    print("="*80)
    print("\nAsking agent to focus on: AI/ML and Infrastructure\n")
    
    briefing = AgentBriefing()
    result = briefing.generate_focused_briefing(
        focus_areas=["AI and machine learning", "computer systems and infrastructure"],
        days=2
    )
    
    print("\n--- FOCUSED BRIEFING START ---\n")
    print(result)
    print("\n--- FOCUSED BRIEFING END ---\n")
    
    return result


def demo_custom_sources():
    """Demo 3: Custom source configuration"""
    print("\n" + "="*80)
    print("DEMO 3: Custom Sources - Tech Only")
    print("="*80)
    print("\nConfiguring agent with tech-focused sources only\n")
    
    tech_sources = [
        {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "type": "rss"},
        {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "type": "rss"},
        {"name": "ArXiv CS", "url": "https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR", "type": "rss"},
    ]
    
    briefing = AgentBriefing(sources=tech_sources)
    result = briefing.generate_briefing(
        days=2,
        include_weather=False,
        include_stocks=False,
        include_astronomy=False
    )
    
    print("\n--- TECH-ONLY BRIEFING START ---\n")
    print(result)
    print("\n--- TECH-ONLY BRIEFING END ---\n")
    
    return result


def demo_comparison():
    """Demo 4: Show the architectural difference"""
    print("\n" + "="*80)
    print("DEMO 4: Architectural Comparison")
    print("="*80)
    print()
    
    print("CONSTRAINED-LLM APPROACH (old):")
    print("  1. Fetch NYT articles")
    print("  2. Format: '[0] Title 1\\n[1] Title 2\\n...'")
    print("  3. Prompt: 'Rank these articles. Return JSON array of top 5 indices.'")
    print("  4. Response: '[3, 7, 12, 1, 18]'")
    print("  5. Extract articles at those indices")
    print("  6. Format into predetermined section")
    print("  7. Repeat for other categories...")
    print("  8. Assemble fixed-order output\n")
    
    print("AGENT-CENTRIC APPROACH (new):")
    print("  1. Fetch all content from all sources")
    print("  2. Format: Structured overview of all available content")
    print("  3. Prompt: 'You are an intelligent editor. Create the best briefing.'")
    print("  4. Response: Complete markdown briefing with agent's chosen structure")
    print("  5. Done!\n")
    
    print("Key differences:")
    print("  • Constrained: Multiple small prompts, rigid structure")
    print("  • Agent-centric: One large prompt, full autonomy")
    print()
    print("  • Constrained: Agent scores/ranks predefined options")
    print("  • Agent-centric: Agent creates, synthesizes, structures")
    print()
    print("  • Constrained: Human decides 'what' and 'how'")
    print("  • Agent-centric: Human decides 'sources', agent decides rest")
    print()


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("AGENT-CENTRIC ARCHITECTURE DEMO")
    print("="*80)
    print("\nThis demonstrates the new architectural approach where the LLM")
    print("has full autonomy to create briefings with its own structure.")
    print()
    
    # Show the comparison first
    demo_comparison()
    
    # Wait for user
    input("\nPress Enter to run Demo 1 (Basic Briefing)...")
    demo_basic_briefing()
    
    input("\nPress Enter to run Demo 2 (Focused Briefing)...")
    demo_focused_briefing()
    
    input("\nPress Enter to run Demo 3 (Custom Sources)...")
    demo_custom_sources()
    
    print("\n" + "="*80)
    print("DEMOS COMPLETE")
    print("="*80)
    print("\nTo use in production:")
    print("  • Run: python daily_workflow_agent.py")
    print("  • Or import: from agent_briefing import AgentBriefing")
    print()


if __name__ == "__main__":
    import sys
    
    # Allow running individual demos
    if len(sys.argv) > 1:
        if sys.argv[1] == "basic":
            demo_basic_briefing()
        elif sys.argv[1] == "focused":
            demo_focused_briefing()
        elif sys.argv[1] == "custom":
            demo_custom_sources()
        elif sys.argv[1] == "compare":
            demo_comparison()
        else:
            print(f"Unknown demo: {sys.argv[1]}")
            print("Options: basic, focused, custom, compare")
    else:
        main()
