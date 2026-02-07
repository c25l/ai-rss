# Architectural Diagrams

## Constrained-LLM Approach (Original)

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSTRAINED-LLM FLOW                      │
└─────────────────────────────────────────────────────────────┘

Step 1: FIXED STRUCTURE (defined in code)
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Weather  │  News    │   Tech   │ Research │  Stocks  │
└──────────┴──────────┴──────────┴──────────┴──────────┘

Step 2: FETCH & FORMAT (per section)
┌───────────────────────────────────────────────────────┐
│  News Articles (50 items)                             │
│  [0] Title 1                                          │
│  [1] Title 2                                          │
│  [2] Title 3                                          │
│  ...                                                  │
│  [49] Title 50                                        │
└───────────────────────────────────────────────────────┘

Step 3: NARROW LLM CALL (ranking only)
┌───────────────────────────────────────────────────────┐
│  LLM Prompt:                                          │
│  "Rank these articles. Return JSON array of top 5."  │
│                                                       │
│  LLM Response:                                        │
│  "[3, 7, 12, 1, 18]"                                 │
└───────────────────────────────────────────────────────┘

Step 4: EXTRACT SELECTED
┌───────────────────────────────────────────────────────┐
│  selected = [articles[3], articles[7], ...]          │
└───────────────────────────────────────────────────────┘

Step 5: FORMAT TO PREDETERMINED STRUCTURE
┌───────────────────────────────────────────────────────┐
│  ## News                                              │
│  - [Title 3](url)                                     │
│  - [Title 7](url)                                     │
│  - [Title 12](url)                                    │
└───────────────────────────────────────────────────────┘

Step 6: REPEAT FOR ALL SECTIONS
    LLM Call 1 → News ranking
    LLM Call 2 → Tech ranking
    LLM Call 3 → Research ranking
    (Multiple small, narrow calls)

Step 7: ASSEMBLE IN FIXED ORDER
┌───────────────────────────────────────────────────────┐
│  # Daily Briefing                                     │
│                                                       │
│  ## Weather Forecast                                  │
│  [predetermined format]                               │
│                                                       │
│  ## News Intelligence Brief                           │
│  [ranked articles in fixed format]                    │
│                                                       │
│  ## Tech News                                         │
│  [ranked articles in fixed format]                    │
│                                                       │
│  ## Research Preprints                                │
│  [ranked articles with AI summary]                    │
│                                                       │
│  ## Market Close Summary                              │
│  [predetermined format]                               │
└───────────────────────────────────────────────────────┘

Characteristics:
• Multiple small LLM calls (5-10)
• Fixed section structure
• LLM only ranks/filters
• ~10-20K tokens total
• Predictable output
```

## Agent-Centric Approach (New)

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT-CENTRIC FLOW                        │
└─────────────────────────────────────────────────────────────┘

Step 1: TOOLS (available to agent)
┌──────────────────┬───────────────────┬────────────────────┐
│ fetch_rss_feed() │ scrape_webpage()  │ fetch_all_sources()│
└──────────────────┴───────────────────┴────────────────────┘

Step 2: FETCH ALL CONTENT (no predetermined structure)
┌───────────────────────────────────────────────────────┐
│  All Sources × All Articles = Complete Content        │
│                                                       │
│  NYT World:        42 articles                        │
│  NYT US:           38 articles                        │
│  The Atlantic:     15 articles                        │
│  Google AI Blog:    3 articles                        │
│  ArXiv CS:         18 articles                        │
│  ...                                                  │
│  Total:           200+ articles                       │
└───────────────────────────────────────────────────────┘

Step 3: FORMAT FOR AGENT (structured context)
┌───────────────────────────────────────────────────────┐
│  ### SOURCE: NYT World News                           │
│  Articles available: 42                               │
│                                                       │
│  1. **Article Title**                                 │
│     URL: https://...                                  │
│     Published: 2026-02-07T08:30:00                    │
│     Summary: First 200 chars...                       │
│                                                       │
│  2. **Another Article**                               │
│     URL: https://...                                  │
│     ...                                               │
│                                                       │
│  ### SOURCE: ArXiv CS                                 │
│  Articles available: 18                               │
│  ...                                                  │
│                                                       │
│  ### AUXILIARY DATA                                   │
│  Weather: High 65°F, Low 42°F                         │
│  Stocks: MSFT +2.3%, NVDA +5.1%                       │
└───────────────────────────────────────────────────────┘

Step 4: SINGLE COMPREHENSIVE LLM CALL
┌───────────────────────────────────────────────────────┐
│  LLM Prompt:                                          │
│  "You are an intelligent briefing editor.            │
│                                                       │
│   YOU DECIDE:                                         │
│   - Which content matters                             │
│   - How to structure briefing                         │
│   - What to synthesize                                │
│   - What connections to draw                          │
│                                                       │
│   Here is ALL available content:                      │
│   [200+ articles across 12 sources]                   │
│   [Weather, stocks, astronomy data]                   │
│                                                       │
│   Create the best possible briefing."                 │
│                                                       │
│  LLM Response:                                        │
│  [Complete markdown briefing - agent's structure]     │
└───────────────────────────────────────────────────────┘

Step 5: DONE! (output from agent)
┌───────────────────────────────────────────────────────┐
│  # Daily Briefing - February 7, 2026                  │
│                                                       │
│  ## The Story of the Day: AI Regulation               │
│  [Agent-written synthesis connecting multiple sources]│
│                                                       │
│  ### Key Developments                                 │
│  **Policy & Regulation**                              │
│  [Agent analysis with inline citations]               │
│                                                       │
│  **Industry Response**                                │
│  [Agent synthesis of related stories]                 │
│                                                       │
│  **Market Implications**                              │
│  [Agent connects tech news to stock data]             │
│                                                       │
│  ## Environmental & Climate                           │
│  [Agent creates this section based on content]        │
│                                                       │
│  ## Research Spotlight                                │
│  [Agent selects and explains relevant papers]         │
│                                                       │
│  ## Local & Regional                                  │
│  [Agent-determined section for local news]            │
│                                                       │
│  ## Weather & Sky                                     │
│  [Agent integrates weather and astronomy]             │
└───────────────────────────────────────────────────────┘

Characteristics:
• Single large LLM call
• Dynamic section structure
• LLM creates/analyzes/synthesizes
• ~50-100K tokens single call
• Adaptive, intelligent output
```

## Decision Tree: Which Approach?

```
                    ┌─────────────────────────┐
                    │ Need Daily Briefing?    │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼────────┐            ┌────────▼────────┐
        │ Constrained-LLM│            │ Agent-Centric   │
        │ (Original)     │            │ (New)           │
        └────────────────┘            └─────────────────┘
                │                               │
                │                               │
    Choose if:                      Choose if:
    ─────────────────              ──────────────────
    ✓ Need consistent format       ✓ Want synthesis
    ✓ Minimize token costs          ✓ Content varies
    ✓ Explicit control              ✓ Adaptive output
    ✓ Well-defined workflow         ✓ Trust AI decisions
    ✓ Easy debugging                ✓ Need analysis
                │                               │
                │                               │
        ┌───────▼────────┐            ┌────────▼────────┐
        │  Run:          │            │  Run:           │
        │  daily_        │            │  daily_         │
        │  workflow.py   │            │  workflow_      │
        │                │            │  agent.py       │
        └────────────────┘            └─────────────────┘
```

## Token Flow Comparison

```
CONSTRAINED-LLM TOKEN USAGE:
┌────────────────────────────────────────────┐
│ Call 1: Rank news      (2K tokens)         │
│ Call 2: Rank tech      (1.5K tokens)       │
│ Call 3: Rank research  (2K tokens)         │
│ Call 4: Summarize      (3K tokens)         │
│ Call 5: More ranking   (1.5K tokens)       │
│ ...                                        │
│ TOTAL: ~10-20K tokens (multiple calls)     │
└────────────────────────────────────────────┘
Cost: Lower, Parallel execution possible

AGENT-CENTRIC TOKEN USAGE:
┌────────────────────────────────────────────┐
│ Single Call:                               │
│   - Input: All content (40K tokens)        │
│   - Output: Complete briefing (10K tokens) │
│   TOTAL: ~50-100K tokens (one call)        │
└────────────────────────────────────────────┘
Cost: Higher, Sequential execution only
```

## Information Flow

```
CONSTRAINED APPROACH:
Sources → Fetch → Format → Rank → Extract → Format → Assemble
   ↓        ↓       ↓       ↓       ↓        ↓         ↓
  NYT     100     [0]     LLM     [3,7]    Links    Fixed
Atlantic  50    [1]       →       [12]      →      Output
ArXiv     30    [2]     JSON    [1,18]    MD

Multiple transformations, rigid pipeline


AGENT APPROACH:
Sources → Fetch → Format → Agent → Output
   ↓        ↓       ↓       ↓        ↓
  NYT     100   Structured  AI    Dynamic
Atlantic  50    Context   Creates  Briefing
ArXiv     30    +Aux      Complete
                Data      Document

Single transformation, flexible pipeline
```

---

**Visual Summary:**
- Constrained: Many small steps, fixed output
- Agent-Centric: Few big steps, flexible output
