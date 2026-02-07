#!/usr/bin/env python
"""
Side-by-side comparison of Constrained-LLM vs Agent-Centric approaches.

This script demonstrates the fundamental architectural difference.
"""

import datetime
from typing import List


def show_constrained_approach():
    """Demonstrate the constrained-LLM approach (original architecture)"""
    print("\n" + "="*80)
    print("CONSTRAINED-LLM APPROACH (Original)")
    print("="*80)
    print("\nPhilosophy: Use LLM sparingly. Don't let it get creative.")
    print()
    
    print("STEP 1: Hard-coded structure")
    print("  sections = ['Weather', 'News', 'Tech', 'Research', 'Stocks']")
    print()
    
    print("STEP 2: Fetch and format content rigidly")
    print("  news_articles = fetch_news()")
    print("  formatted = format_as_numbered_list(news_articles)")
    print("  # Example output:")
    print("  # [0] Article Title 1")
    print("  # [1] Article Title 2")
    print("  # [2] Article Title 3")
    print()
    
    print("STEP 3: Use LLM ONLY for ranking (narrow task)")
    print("  prompt = '''Rank these articles. Return JSON array of top 5 indices.'''")
    print("  response = llm.generate(prompt + formatted)")
    print("  # Response: '[3, 7, 12, 1, 18]'")
    print()
    
    print("STEP 4: Extract selected items")
    print("  selected = [news_articles[i] for i in response_indices]")
    print()
    
    print("STEP 5: Format into predetermined section")
    print("  output = '## News\\n' + format_links(selected)")
    print()
    
    print("STEP 6: Repeat for each section (Tech, Research, etc.)")
    print("  # Multiple narrow LLM calls, each returning indices")
    print()
    
    print("STEP 7: Assemble in fixed order")
    print("  final = weather + news + tech + research + stocks")
    print()
    
    print("KEY CHARACTERISTICS:")
    print("  ✓ Human defines: structure, sections, format, order")
    print("  ✓ LLM only scores/ranks pre-formatted options")
    print("  ✓ Multiple small prompts with specific outputs")
    print("  ✓ Highly predictable and consistent")
    print("  ✓ Lower token usage (10-20K total)")
    print("  ✓ Easier to debug and control")


def show_agent_centric_approach():
    """Demonstrate the agent-centric approach (new architecture)"""
    print("\n" + "="*80)
    print("AGENT-CENTRIC APPROACH (New)")
    print("="*80)
    print("\nPhilosophy: Give agent tools and sources. Let it decide everything.")
    print()
    
    print("STEP 1: Provide tools (no predetermined structure)")
    print("  tools = {")
    print("    'fetch_rss_feed': function_to_fetch_rss,")
    print("    'scrape_webpage': function_to_scrape,")
    print("    'fetch_all_sources': function_to_fetch_all")
    print("  }")
    print()
    
    print("STEP 2: Fetch all content from all sources")
    print("  all_content = tools.fetch_all_sources(source_list)")
    print("  # Returns: Dict[source_name, List[Article]]")
    print()
    
    print("STEP 3: Format content for agent comprehension")
    print("  formatted = '''")
    print("  ### SOURCE: NYT World News")
    print("  Articles available: 42")
    print("  1. **Article Title** (url) - Summary preview...")
    print("  2. **Another Article** (url) - Summary preview...")
    print("  ...'")
    print()
    
    print("STEP 4: Single comprehensive prompt with full autonomy")
    print("  prompt = '''")
    print("  You are an intelligent briefing editor.")
    print("  ")
    print("  YOU DECIDE:")
    print("  - Which content is important")
    print("  - How to structure the briefing")
    print("  - What to synthesize and connect")
    print("  - What analysis to add")
    print("  ")
    print("  Here is all available content:")
    print("  {formatted_content}")
    print("  ")
    print("  Create the best possible briefing.")
    print("  '''")
    print()
    
    print("STEP 5: Agent generates complete briefing")
    print("  briefing = llm.generate(prompt)")
    print("  # Agent returns: Complete markdown briefing with its chosen structure")
    print()
    
    print("STEP 6: Done! (no assembly needed)")
    print("  return briefing")
    print()
    
    print("KEY CHARACTERISTICS:")
    print("  ✓ Agent decides: structure, sections, importance, presentation")
    print("  ✓ LLM creates, synthesizes, analyzes, connects")
    print("  ✓ Single large prompt with open-ended task")
    print("  ✓ Adaptive and intelligent output")
    print("  ✓ Higher token usage (50-100K single call)")
    print("  ✓ More creative and context-aware")


def show_prompt_comparison():
    """Show actual prompt examples side by side"""
    print("\n" + "="*80)
    print("PROMPT COMPARISON")
    print("="*80)
    
    print("\nCONSTRAINED-LLM PROMPT (for ranking news):")
    print("-" * 60)
    print("""Rank these news story clusters by importance and significance.
Focus on: major news impact, public interest, and relevance.

[0] Climate summit reaches agreement (5 new articles today, 23 total)
[1] Local election results finalized (2 articles)
[2] Tech company announces layoffs (8 new articles today, 15 total)
... (45 more items)

Respond with ONLY a JSON array of the top 5 indices (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array.""")
    
    print("\n\nAGENT-CENTRIC PROMPT (for full briefing):")
    print("-" * 60)
    print("""You are an intelligent briefing editor for 2026-02-07.

You have access to content from multiple sources (news, tech, research, etc.).
Your job is to CREATE A COMPREHENSIVE DAILY BRIEFING with COMPLETE AUTONOMY.

YOU DECIDE:
- Which stories/articles are most important
- How to structure the briefing (create your own sections)
- What context to add or synthesize
- How to present information (summaries, lists, analysis)
- What connections to draw between different topics
- The overall narrative and flow

AVAILABLE CONTENT:

### SOURCE: NYT World News
Articles available: 42

1. **Climate summit reaches historic agreement on carbon targets**
   URL: https://nyt.com/...
   Published: 2026-02-07T08:30:00
   Summary: World leaders agreed to new binding carbon reduction targets...

2. **Tech sector braces for regulatory changes in EU**
   URL: https://nyt.com/...
   Published: 2026-02-07T07:15:00
   Summary: European Union proposes sweeping changes to AI regulation...

... (200+ more articles from 12 sources)

### SOURCE: ArXiv CS
Articles available: 15

1. **Efficient Distributed Training at Exascale**
   URL: https://arxiv.org/...
   Summary: We present a novel approach to distributed training...

... (more sources)

AUXILIARY DATA:

### WEATHER DATA
High: 65°F, Low: 42°F. Partly cloudy. 10% chance of rain.

### STOCK MARKET DATA
MSFT: $425.30 (+2.3%), NVDA: $920.15 (+5.1%), S&P 500: 5,847.20 (+1.2%)

Now, create the best possible daily briefing. Structure it however you think works best.
Use markdown formatting. Be creative and insightful.""")


def show_output_comparison():
    """Show example outputs from each approach"""
    print("\n" + "="*80)
    print("OUTPUT COMPARISON")
    print("="*80)
    
    print("\nCONSTRAINED-LLM OUTPUT:")
    print("-" * 60)
    print("""# Daily Weather, Space & Sky Summary

## Weather Forecast
High: 65°F, Low: 42°F. Partly cloudy...

## Space Weather
Solar wind speed: 450 km/s, Kp-index: 2...

## Tonight's Sky
Moon: Waxing Crescent (35% illuminated)...

---

# Daily News Intelligence Brief

## Continuing Coverage
- **[Climate summit reaches agreement](url)** (5 new articles today, 23 total)
- **[Tech company announces layoffs](url)** (8 new articles today, 15 total)

## New Today
- **[Local election results](url)** (2 articles)

---

# Tech News
- **[EU proposes AI regulation](url)**
- **[Microsoft announces new AI model](url)**
...

---

# Research Preprints
[5 selected papers on distributed systems and AI infrastructure]

---

# Market Close Summary
MSFT: $425.30 (+2.3%)...""")
    
    print("\n\nAGENT-CENTRIC OUTPUT:")
    print("-" * 60)
    print("""# Daily Briefing - February 7, 2026

## The Story of the Day: AI Regulation Takes Center Stage

The tech world is bracing for significant regulatory shifts as the EU moves 
forward with comprehensive AI governance proposals. This coincides with major 
industry developments at Microsoft and implications for market valuations...

### Key Developments

**Policy & Regulation**
The European Union's proposed AI regulation framework represents the most 
significant attempt yet to govern artificial intelligence systems. The timing 
is notable given [recent industry consolidation](url) and [research advances 
in distributed training](https://arxiv.org/abs/2026.12345) that have concentrated AI capabilities...

**Industry Response**  
Tech giants are positioning themselves ahead of these changes. [Microsoft's 
new AI model announcement](url) appears strategically timed. Meanwhile, 
[layoffs at major tech companies](url) may reflect cost optimization before 
regulatory compliance expenses...

**Market Implications**
Tech stocks rallied today (MSFT +2.3%, NVDA +5.1%) despite regulatory 
uncertainty, suggesting investors view regulation as potentially creating 
moats for incumbent players...

## Environmental & Climate

The climate summit's [historic carbon reduction agreement](url) marks a shift 
from voluntary to binding commitments. Notably, [recent research on renewable 
energy systems](https://arxiv.org/abs/2026.23456) suggests these targets are technologically feasible...

## Local & Regional

[Local election results](url) finalized today with implications for...

## Research Spotlight

Several papers this week deserve attention:
1. [Efficient Distributed Training at Exascale](https://arxiv.org/abs/2026.11111) - Novel approach 
   enabling training of models 10x larger than current limits
2. [Real-time Performance Monitoring](https://arxiv.org/abs/2026.22222) - Could address regulatory 
   compliance needs mentioned above

## Weather & Sky
Partly cloudy, high 65°F, low 42°F. Tonight: waxing crescent moon at 35% 
illumination, excellent viewing conditions for Venus and Jupiter...""")


def main():
    """Run the comparison demonstrations"""
    print("\n" + "="*80)
    print("ARCHITECTURAL COMPARISON: Constrained-LLM vs Agent-Centric")
    print("="*80)
    
    show_constrained_approach()
    input("\n\nPress Enter to see Agent-Centric approach...")
    
    show_agent_centric_approach()
    input("\n\nPress Enter to compare prompts...")
    
    show_prompt_comparison()
    input("\n\nPress Enter to compare outputs...")
    
    show_output_comparison()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("WHEN TO USE CONSTRAINED-LLM:")
    print("  • Need consistent, predictable output format")
    print("  • Want to minimize token usage and costs")
    print("  • Prefer explicit control over structure")
    print("  • Have well-defined categories and workflows")
    print()
    print("WHEN TO USE AGENT-CENTRIC:")
    print("  • Want intelligent synthesis and connections")
    print("  • Content varies significantly day-to-day")
    print("  • Value adaptive, context-aware presentation")
    print("  • Trust AI to make editorial decisions")
    print("  • Need deeper analysis, not just filtering")
    print()
    print("Both approaches are valid - choose based on your needs!")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "constrained":
            show_constrained_approach()
        elif sys.argv[1] == "agent":
            show_agent_centric_approach()
        elif sys.argv[1] == "prompts":
            show_prompt_comparison()
        elif sys.argv[1] == "outputs":
            show_output_comparison()
        else:
            print("Usage: python compare_architectures.py [constrained|agent|prompts|outputs]")
    else:
        main()
