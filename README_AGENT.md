# Agent-Centric Daily Briefing System

A Python system that uses an AI agent as a **content curator** to create intelligent daily briefings from multiple sources.

## Philosophy

This implements an **agent-centric architecture** where the AI acts as a CURATOR, not a writer:
- **Curate**: Select and organize the most important content
- **Cite**: Link directly to original sources with inline citations
- **Connect**: Show relationships with minimal bridging text
- **Preserve**: Pass through original text from sources, don't rewrite

The agent's role is **CURATION and CITATION**, not text generation. Content should flow from upstream sources with the agent providing intelligent organization and selection.

This contrasts with traditional **constrained-LLM** approaches that only use AI for scoring/ranking within a rigid, predetermined structure.

## Quick Start

```python
from agent_briefing import AgentBriefing

# Create briefing system with default sources
briefing = AgentBriefing()

# Generate a curated briefing with enhanced multi-step reasoning
result = briefing.generate_briefing(days=1, use_enhanced_prompting=True)
print(result)
```

## Features

### Agent as Curator
The agent receives:
- **Tools**: RSS feed reader, web scraper, weather APIs, space weather APIs, astronomy APIs
- **Sources**: List of sites to monitor (including TLDR Tech, Hacker News Daily)
- **API data**: Real-time weather, space conditions, astronomical viewing
- **Multi-step reasoning**: Structured curation approach with example format

The agent then autonomously:
- Analyzes all available content
- Identifies important stories
- Selects key excerpts from sources
- Structures sections logically
- Cites all sources with inline links
- Uses minimal bridging text to show connections

**Key principle**: The agent curates and cites, using direct quotes/excerpts from sources rather than writing summaries or analysis.

### API-Based Tools (NEW)

The agent now has access to real-time API tools:

```python
from agent_briefing import AgentTools

# Weather forecast
weather = AgentTools.get_weather_forecast(lat=40.165729, lon=-105.101194)

# Space weather conditions
space = AgentTools.get_space_weather()

# Astronomical viewing for tonight
astronomy = AgentTools.get_astronomy_viewing(lat=40.1672, lon=-105.1019)

# TLDR Tech newsletter
tldr = AgentTools.fetch_tldr_tech()

# Hacker News Daily digest
hn = AgentTools.fetch_hacker_news_daily()
```

### Enhanced Multi-Step Reasoning (NEW)

The system now supports enhanced prompting with:
- **Structured thinking**: 4-step reasoning process (identify themes → prioritize → structure → add value)
- **Example format**: Shows agent how to structure output
- **Tool integration**: Guides agent on using API data effectively
- **Connection emphasis**: Encourages synthesis across domains

```python
# Use enhanced prompting (recommended)
result = briefing.generate_briefing(
    days=1,
    use_enhanced_prompting=True  # Multi-step reasoning with examples
)

# Use simple prompting
result = briefing.generate_briefing(
    days=1,
    use_enhanced_prompting=False  # Original simple prompt
)
```

### Flexible Configuration

```python
# Custom sources
custom_sources = [
    {"name": "My Blog", "url": "https://example.com/feed", "type": "rss"},
    {"name": "Dashboard", "url": "https://dashboard.com", "type": "scrape"}
]

briefing = AgentBriefing(sources=custom_sources)
```

### Focused Briefings

```python
# Generate briefing focused on specific topics
result = briefing.generate_focused_briefing(
    focus_areas=["AI research", "local politics"],
    days=2
)
```

## Architecture

### Components

1. **AgentBriefing**: Main class orchestrating the briefing generation
2. **AgentTools**: Toolkit for the agent (RSS, scraping, fetching)
3. **Copilot**: LLM interface for agent reasoning

### Data Flow

```
Sources Config → AgentTools.fetch_all_sources() → Raw Articles
                                                      ↓
Raw Articles → Format for Agent → Structured Content List
                                        ↓
Structured Content + Auxiliary Data → Agent Prompt
                                        ↓
                              Agent Analysis & Generation
                                        ↓
                              Final Briefing (Markdown)
```

### Agent Prompt Structure

The agent receives a comprehensive prompt that includes:
1. Role definition ("intelligent briefing editor")
2. Explicit autonomy grant
3. Guidelines (not rules)
4. All available content in structured format
5. Auxiliary data when applicable
6. Open-ended task ("create the best briefing")

## Usage Examples

### Example 1: Daily Briefing

```python
from agent_briefing import AgentBriefing

briefing = AgentBriefing()
result = briefing.generate_briefing(
    days=1,
    include_weather=True,
    include_stocks=True,
    include_astronomy=True
)
print(result)
```

### Example 2: Tech-Only Briefing

```python
tech_sources = [
    {"name": "ArXiv", "url": "https://export.arxiv.org/rss/cs", "type": "rss"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "type": "rss"},
]

briefing = AgentBriefing(sources=tech_sources)
result = briefing.generate_briefing(days=2, include_weather=False)
```

### Example 3: Focused Analysis

```python
briefing = AgentBriefing()
result = briefing.generate_focused_briefing(
    focus_areas=["climate policy", "renewable energy"],
    days=3
)
```

### Example 4: Production Workflow

```python
#!/usr/bin/env python
import datetime
from agent_briefing import AgentBriefing
from emailer import Emailer

# Generate briefing
briefing_system = AgentBriefing()
content = briefing_system.generate_briefing(days=1)

# Send via email
today = datetime.datetime.now().strftime("%Y-%m-%d")
subject = f"Daily Briefing - {today}"

emailer = Emailer()
emailer.send_email(content, subject=subject)
```

## Default Sources

The system comes configured with diverse sources:

**News**: NYT, The Atlantic, Heather Cox Richardson, MetaFilter, ACOUP, local news
**Tech**: Microsoft Research, Google AI Blog  
**Research**: ArXiv (distributed systems, performance, architecture)

All sources can be customized.

**New in this version:**
- **TLDR Tech & AI newsletters** - Curated daily tech news digests
- **Hacker News Daily** - Top stories from HN in digest form
- **API-based tools** - Real-time weather, space weather, astronomy data

## Comparison: Agent-Centric vs. Constrained-LLM

### Constrained-LLM Approach
```python
# Multiple narrow prompts
rankings1 = llm.rank("Rank these 50 articles, return top 5 indices")
rankings2 = llm.rank("Rank these 30 articles, return top 7 indices")
# ... assemble into fixed structure
```

**Characteristics:**
- Fixed section structure
- AI only scores/ranks
- Predetermined output format
- Lower token usage
- Very consistent output

### Agent-Centric Approach (Enhanced)
```python
# Single comprehensive prompt with multi-step reasoning
briefing = llm.generate("""
You're an intelligent editor. Follow this approach:
1. Identify key themes
2. Prioritize & synthesize
3. Structure your briefing
4. Add value

Here's all content + API data. Create the best briefing.
""")
```

**Characteristics:**
- Dynamic section structure
- AI creates and synthesizes
- Adaptive output format with guided structure
- Higher token usage
- Variable but intelligent output
- **NEW**: Multi-step reasoning with examples

## Requirements

- Python 3.8+
- **GitHub Copilot CLI** (`copilot` command) - [Install instructions](https://github.com/github/gh-copilot)
- Dependencies in `requirements.txt`:
  - feedparser (RSS parsing)
  - beautifulsoup4 (web scraping)
  - requests (HTTP requests)
  - ephem (astronomy calculations)

**LLM Backend:**
- Uses **GitHub Copilot CLI locally** with **gpt-5.2** by default
- No external API calls - all LLM interactions via Copilot CLI
- Model can be configured via `COPILOT_MODEL` environment variable

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install GitHub Copilot CLI (if not already installed)
# See: https://github.com/github/gh-copilot

# Configure model (optional - defaults to gpt-5.2)
export COPILOT_MODEL=gpt-5.2
```

## Testing

```bash
# Run comparison demo
python demo_agent_architecture.py compare

# Run full demo suite
python demo_agent_architecture.py

# Run simple example
python example_usage.py
```

## Performance

**Token Usage**: 50-100K tokens per briefing (single large call)
**Time**: 3-8 minutes depending on content volume and LLM speed
**Cost**: Higher than constrained approach but more intelligent output

## Customization

### Add Custom Sources

```python
sources = [
    {"name": "Custom RSS", "url": "https://example.com/feed", "type": "rss"},
    {"name": "Custom Page", "url": "https://example.com", "type": "scrape"},
]

briefing = AgentBriefing(sources=sources)
```

### Modify Agent Behavior

Edit the agent prompt in `agent_briefing.py` → `generate_briefing()` method.

### Add New Tools

Extend `AgentTools` class with new methods:

```python
class AgentTools:
    @staticmethod
    def fetch_api_data(api_url: str) -> Dict:
        # Your implementation
        pass
```

## Best Practices

1. **Trust the Agent**: Don't over-constrain the prompt
2. **Provide Context**: More sources = better decisions
3. **Review Output**: Agent output varies, spot-check important briefings
4. **Adjust Focus**: Use `generate_focused_briefing()` for specific needs
5. **Monitor Costs**: Large prompts = higher token usage

## Troubleshooting

**Issue**: Agent output is inconsistent
- **Solution**: This is expected - agent has creative freedom. Add guidelines to prompt if needed.

**Issue**: Briefing is too long/short
- **Solution**: Modify agent prompt to specify desired length

**Issue**: Agent misses important content
- **Solution**: Ensure sources contain that content, or add it to focus_areas

**Issue**: High token costs
- **Solution**: Consider constrained-LLM approach for routine briefings

## Future Enhancements

Potential improvements:
- Multi-step reasoning (agent requests additional sources)
- Tool use during generation (not just upfront)
- Memory of previous briefings
- User preference learning
- Confidence scoring
- Interactive querying

## License

Same as parent repository.

## See Also

- `ARCHITECTURE.md` - Detailed architectural documentation
- `daily_workflow_agent.py` - Production workflow implementation  
- `demo_agent_architecture.py` - Interactive demos
- `daily_workflow.py` - Original constrained-LLM implementation for comparison
