#!/usr/bin/env python
"""
Simple example showing how to use the agent-centric briefing system.

Run this to see a quick demo of the new architecture.
"""

from agent_briefing import AgentBriefing

# Example 1: Basic usage with defaults
print("Example 1: Basic Briefing")
print("-" * 60)

briefing_system = AgentBriefing()
result = briefing_system.generate_briefing(days=1)
print(result)

print("\n\n")

# Example 2: Custom sources
print("Example 2: Custom Tech-Focused Sources")
print("-" * 60)

custom_sources = [
    {"name": "ArXiv", "url": "https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR", "type": "rss"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "type": "rss"},
]

tech_briefing = AgentBriefing(sources=custom_sources)
tech_result = tech_briefing.generate_briefing(
    days=2,
    include_weather=False,
    include_stocks=False,
    include_astronomy=False
)
print(tech_result)

print("\n\n")

# Example 3: Focused briefing
print("Example 3: Focused on AI Research")
print("-" * 60)

focused_result = briefing_system.generate_focused_briefing(
    focus_areas=["artificial intelligence", "machine learning systems"],
    days=2
)
print(focused_result)
