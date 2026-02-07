# Agent-Centric Architecture

This repository now supports **two distinct architectural approaches** for generating daily briefings:

## 1. Constrained-LLM Approach (Original)

**File:** `daily_workflow.py`

**Philosophy:** Use the LLM as sparingly as possible. Don't let it get creative.

**Characteristics:**
- ✓ Hard-coded section structure (Weather, News, Tech, Research, Stocks)
- ✓ LLM only used for **ranking/filtering** pre-formatted content
- ✓ Rigid output format predetermined by code
- ✓ Minimal AI decision-making - just scoring/selecting from lists
- ✓ Human defines the structure, AI fills in the blanks

**Example Flow:**
```
1. Fetch articles from hard-coded feeds
2. Format articles into fixed structure
3. Ask LLM: "Rank these 50 news clusters, return top 5 indices"
4. Ask LLM: "Rank these 20 tech articles, return top 7 indices"
5. Assemble pre-defined sections in fixed order
6. Send email
```

## 2. Agent-Centric Approach (New)

**File:** `daily_workflow_agent.py` / `agent_briefing.py`

**Philosophy:** Give the agent tools and sources. Let it decide everything else.

**Characteristics:**
- ✓ Agent has **full editorial autonomy**
- ✓ Tools provided: RSS feed reader, web scraper
- ✓ Sources provided: List of sites to monitor
- ✓ Agent decides: what matters, how to structure, what to synthesize
- ✓ Dynamic section creation based on discovered content
- ✓ Agent can draw connections, add analysis, create narrative flow
- ✓ No predetermined output structure

**Example Flow:**
```
1. Give agent access to tools (fetch_rss_feed, scrape_webpage)
2. Give agent list of sources to monitor
3. Give agent auxiliary data (weather, stocks, astronomy)
4. Single prompt: "You're an intelligent editor. Create the best briefing."
5. Agent analyzes everything, decides structure, writes briefing
6. Send email
```

## Architectural Comparison

| Aspect | Constrained-LLM | Agent-Centric |
|--------|----------------|---------------|
| **LLM Role** | Scorer/Filter | Creative Editor |
| **Structure** | Fixed by code | Decided by agent |
| **Creativity** | Minimal | Maximal |
| **Autonomy** | Low | High |
| **Prompt Type** | Task-specific (rank these) | Open-ended (create briefing) |
| **Output Format** | Predetermined | Dynamic |
| **Token Usage** | Lower | Higher |
| **Consistency** | Very high | Variable |
| **Adaptability** | Low | High |

## Why Two Approaches?

Each approach has trade-offs:

**Constrained-LLM Advantages:**
- Predictable output structure
- Lower token usage / cost
- Faster execution (parallel ranking tasks)
- Easier to debug
- Consistent format

**Agent-Centric Advantages:**
- More intelligent synthesis
- Better at identifying connections
- Adaptive to content variations
- Can provide deeper analysis
- More natural narrative flow
- Handles novel situations better

## Usage

### Constrained Approach
```bash
python daily_workflow.py
```

### Agent-Centric Approach
```bash
python daily_workflow_agent.py
```

## Customization

### Constrained Approach
Customize by editing code:
- Add/remove sections in `daily_workflow.py`
- Modify ranking prompts in `news.py`, `tech_news.py`, `research.py`
- Change feed sources in respective modules

### Agent-Centric Approach
Customize by configuration:
```python
from agent_briefing import AgentBriefing

# Custom sources
sources = [
    {"name": "My Blog", "url": "https://example.com/feed", "type": "rss"},
    {"name": "Dashboard", "url": "https://example.com/stats", "type": "scrape"}
]

briefing = AgentBriefing(sources=sources)
result = briefing.generate_briefing(days=1)
```

Or create focused briefings:
```python
result = briefing.generate_focused_briefing(
    focus_areas=["AI research", "local politics"],
    days=2
)
```

## Implementation Details

### Tools Available to Agent

**AgentTools** class provides:

1. **fetch_rss_feed(url, days)** - Fetch and parse RSS feeds
2. **scrape_webpage(url)** - Extract content from web pages
3. **fetch_all_sources(sources, days)** - Batch fetch from multiple sources

### Agent Prompt Design

The agent-centric approach uses a single, comprehensive prompt that:
1. Explains the agent's role as "intelligent briefing editor"
2. Grants explicit autonomy over structure and content
3. Provides all available content in structured format
4. Includes auxiliary data (weather, stocks, astronomy)
5. Sets guidelines but not rigid rules
6. Encourages synthesis and connections

### Content Formatting

Raw content is formatted for agent consumption:
```
### SOURCE: NYT World News
Articles available: 42

1. **Article Title Here**
   URL: https://...
   Published: 2026-02-07
   Summary: First 200 chars...
```

This gives the agent enough context to make informed decisions.

## Performance Considerations

**Constrained-LLM:**
- Multiple small LLM calls (5-10 calls)
- Parallel execution possible
- ~2-5 minutes total
- ~10-20K tokens total

**Agent-Centric:**
- One large LLM call
- Sequential execution
- ~3-8 minutes total
- ~50-100K tokens for single call
- Output size varies with agent's decisions

## Future Enhancements

Potential improvements for agent-centric approach:

1. **Multi-step reasoning:** Let agent request additional sources based on initial analysis
2. **Tool use:** Give agent ability to call tools during generation (not just upfront)
3. **Memory:** Allow agent to reference previous briefings for continuity
4. **Feedback loop:** Learn from user preferences over time
5. **Confidence scoring:** Agent indicates uncertainty for human review
6. **Interactive mode:** User can query agent about briefing content

## Philosophical Notes

The shift from constrained-LLM to agent-centric represents a fundamental change in how we think about AI assistance:

**Constrained:** "AI is a tool we control precisely"
- We define the task narrowly
- We structure the input/output
- We verify each step
- AI fills in specific gaps

**Agent-Centric:** "AI is a collaborator we trust broadly"
- We define the goal generally  
- We provide resources and context
- We evaluate the final output
- AI owns the whole process

Neither is inherently "better" - they serve different needs and reflect different comfort levels with AI autonomy.

## License

Same as parent repository.
