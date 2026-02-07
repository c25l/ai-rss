#!/usr/bin/env python
"""
Demo of enhanced agent-centric features:
- API-based tools
- TLDR and Hacker News sources
- Multi-step reasoning with example format
"""

from agent_briefing import AgentBriefing, AgentTools
import datetime


def demo_api_tools():
    """Demo 1: New API-based tools"""
    print("\n" + "="*80)
    print("DEMO 1: API-Based Tools")
    print("="*80)
    print("\nThe agent now has access to real-time API data:\n")
    
    # Weather
    print("1. Fetching weather forecast...")
    try:
        weather = AgentTools.get_weather_forecast()
        print(f"   ✓ Weather data: {weather.get('forecast_text', 'N/A')[:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Space weather
    print("\n2. Fetching space weather...")
    try:
        space = AgentTools.get_space_weather()
        print(f"   ✓ Space weather: {space.get('forecast', 'N/A')[:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Astronomy
    print("\n3. Fetching astronomy viewing info...")
    try:
        astro = AgentTools.get_astronomy_viewing()
        print(f"   ✓ Tonight's sky: {astro.get('viewing_info', 'N/A')[:100]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*80)


def demo_new_sources():
    """Demo 2: TLDR and Hacker News sources"""
    print("\n" + "="*80)
    print("DEMO 2: TLDR Tech & Hacker News Daily")
    print("="*80)
    print("\nFetching from new sources:\n")
    
    # TLDR
    print("1. Fetching TLDR Tech newsletter...")
    try:
        tldr = AgentTools.fetch_tldr_tech()
        print(f"   ✓ Found {len(tldr)} articles from TLDR")
        if tldr:
            print(f"   Example: {str(tldr[0].title)[:80]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Hacker News
    print("\n2. Fetching Hacker News Daily...")
    try:
        hn = AgentTools.fetch_hacker_news_daily()
        print(f"   ✓ Found {len(hn)} articles from HN Daily")
        if hn:
            print(f"   Example: {str(hn[0].title)[:80]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*80)


def demo_multi_step_reasoning():
    """Demo 3: Multi-step reasoning comparison"""
    print("\n" + "="*80)
    print("DEMO 3: Multi-Step Reasoning vs Simple Prompting")
    print("="*80)
    print("\nComparing two prompting approaches:\n")
    
    print("SIMPLE PROMPTING:")
    print("-" * 60)
    print("""
Prompt structure:
  "You are an intelligent editor. Create the best briefing."
  
Characteristics:
  • Single open-ended instruction
  • No structured guidance
  • Agent decides everything freely
  • May vary significantly in approach
""")
    
    print("\nENHANCED MULTI-STEP REASONING:")
    print("-" * 60)
    print("""
Prompt structure:
  STEP 1: IDENTIFY KEY THEMES
    - Scan for patterns and connections
  
  STEP 2: PRIORITIZE & SYNTHESIZE
    - Rank by importance, group related stories
  
  STEP 3: STRUCTURE YOUR BRIEFING
    - Create logical sections based on themes
  
  STEP 4: ADD VALUE
    - Provide context, draw connections
  
  [Example output format provided]

Characteristics:
  • Structured 4-step approach
  • Example format guides output
  • Emphasizes synthesis and connections
  • More consistent high-quality results
""")
    
    print("\n" + "="*80)


def demo_full_briefing():
    """Demo 4: Generate a briefing with all enhancements"""
    print("\n" + "="*80)
    print("DEMO 4: Full Briefing with Enhanced Features")
    print("="*80)
    print("\nGenerating briefing with:")
    print("  • All 14 default sources (including TLDR & HN)")
    print("  • API-based weather, space, astronomy data")
    print("  • Multi-step reasoning with example format")
    print()
    
    try:
        briefing = AgentBriefing()
        
        # Show sources
        print(f"Configured sources: {len(briefing.sources)}")
        for source in briefing.sources:
            print(f"  - {source['name']} ({source['type']})")
        
        print("\nNote: Full generation requires API credentials and takes 3-8 minutes.")
        print("This demo shows the setup. To run full generation:")
        print()
        print("  from agent_briefing import AgentBriefing")
        print("  briefing = AgentBriefing()")
        print("  result = briefing.generate_briefing(")
        print("      days=1,")
        print("      use_enhanced_prompting=True  # Multi-step reasoning")
        print("  )")
        print("  print(result)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    print("\n" + "="*80)


def demo_comparison():
    """Demo 5: Show architectural evolution"""
    print("\n" + "="*80)
    print("DEMO 5: Architectural Evolution")
    print("="*80)
    print()
    
    print("ORIGINAL AGENT-CENTRIC (v1):")
    print("-" * 60)
    print("Sources: 12 RSS feeds")
    print("Tools: fetch_rss_feed(), scrape_webpage()")
    print("Data: Pre-formatted weather/astronomy text")
    print("Prompt: Simple open-ended instruction")
    print("Result: Good but inconsistent structure")
    print()
    
    print("ENHANCED AGENT-CENTRIC (v2 - CURRENT):")
    print("-" * 60)
    print("Sources: 14 sources (added TLDR, HN Daily)")
    print("Tools: + get_weather_forecast(), get_space_weather(),")
    print("       get_astronomy_viewing(), fetch_tldr_tech(),")
    print("       fetch_hacker_news_daily()")
    print("Data: Real-time API calls for weather/space/astronomy")
    print("Prompt: Multi-step reasoning with example format")
    print("Result: Structured yet flexible, better synthesis")
    print()
    
    print("KEY IMPROVEMENTS:")
    print("  ✓ API-based tools for real-time data")
    print("  ✓ Curated tech news sources (TLDR, HN)")
    print("  ✓ Guided multi-step reasoning")
    print("  ✓ Example output format")
    print("  ✓ Better cross-domain synthesis")
    
    print("\n" + "="*80)


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("ENHANCED AGENT-CENTRIC FEATURES DEMO")
    print("="*80)
    print("\nThis demonstrates the new enhancements:")
    print("  1. API-based tools for real-time data")
    print("  2. TLDR Tech & Hacker News Daily sources")
    print("  3. Multi-step reasoning with examples")
    print()
    
    # Run demos
    demo_api_tools()
    
    input("\nPress Enter to continue...")
    demo_new_sources()
    
    input("\nPress Enter to continue...")
    demo_multi_step_reasoning()
    
    input("\nPress Enter to continue...")
    demo_full_briefing()
    
    input("\nPress Enter to continue...")
    demo_comparison()
    
    print("\n" + "="*80)
    print("DEMOS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  • Run: python daily_workflow_agent.py")
    print("  • Or import and use in your code")
    print("  • See README_AGENT.md for full documentation")
    print()


if __name__ == "__main__":
    import sys
    
    # Allow running individual demos
    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            demo_api_tools()
        elif sys.argv[1] == "sources":
            demo_new_sources()
        elif sys.argv[1] == "reasoning":
            demo_multi_step_reasoning()
        elif sys.argv[1] == "briefing":
            demo_full_briefing()
        elif sys.argv[1] == "compare":
            demo_comparison()
        else:
            print(f"Unknown demo: {sys.argv[1]}")
            print("Options: api, sources, reasoning, briefing, compare")
    else:
        main()
