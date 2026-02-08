# Enhancement Features Guide

This document describes the new enhancement features added to the agent-centric briefing system.

## New Features

### 1. Wikipedia Context Integration

The agent can now fetch Wikipedia summaries to provide historical context for people, organizations, events, or concepts mentioned in the news.

**Usage:**
```python
from agent_briefing import AgentTools

# Get context about a topic
context = AgentTools.get_wikipedia_summary("NATO")
print(context['summary'])
print(context['url'])
```

**In the agent:**
The agent is informed about this tool and can optionally use it when generating briefings. It's particularly useful for:
- Background on political figures
- Historical context for organizations
- Explanations of technical concepts
- Context for international events

**Control via preferences:**
```yaml
content_preferences:
  include_wikipedia_context: true  # Enable Wikipedia lookups
```

### 2. User Preferences System

A flexible preferences system allows you to customize briefing generation.

**Setup:**
1. Copy `preferences.yaml.example` to `preferences.yaml`
2. Customize your preferences
3. The system automatically loads them

**Available preferences:**

#### Focus Areas
Tell the agent what topics to emphasize:
```yaml
focus_areas:
  - AI and machine learning
  - Climate and environment
  - International relations
```

#### Exclude Topics
De-emphasize or filter out certain topics:
```yaml
exclude_topics:
  - Sports
  - Celebrity news
```

#### Preferred Sources
Prioritize certain sources:
```yaml
preferred_sources:
  - The Atlantic
  - ArXiv
  - TLDR Tech
```

#### Content Preferences
Control various aspects:
```yaml
content_preferences:
  max_articles_per_section: 5
  include_wikipedia_context: true
  hybrid_research_ranking: true  # Use special ranking for research
  geographic_focus: "United States"
```

#### Research Preferences
Configure research paper handling:
```yaml
research_preferences:
  max_research_papers: 10
  research_categories:
    - cs.AI
    - cs.LG
  use_original_ranking: true  # Use proven ranking algorithm
```

### 3. Hybrid Research Ranking

For research papers (e.g., from ArXiv), you can use a hybrid approach:
- Agent curates most content (news, articles, etc.)
- Research papers use the proven ranking algorithm from the original constrained approach

This combines the best of both worlds:
- Agent's intelligent synthesis for news
- Algorithmic ranking for research papers

**Enable via preferences:**
```yaml
content_preferences:
  hybrid_research_ranking: true

research_preferences:
  max_research_papers: 10
  use_original_ranking: true
```

**How it works:**
1. Research papers are detected by source name (e.g., "ArXiv CS")
2. Papers are ranked using the `rank_items()` method
3. Top-K papers are selected based on novelty, impact, and relevance
4. These ranked papers are then provided to the agent for final curation

### 4. Bluesky Feed Integration

The agent can now fetch posts from Bluesky (AT Protocol) social network feeds.

**Usage:**
Add Bluesky feeds to your `preferences.yaml`:

```yaml
sources:
  # Bluesky sources
  - name: "Bluesky Official"
    url: "bsky.app"
    type: "bluesky"
    limit: 10  # Optional: number of posts to fetch (default: 20)
    
  - name: "Tech Influencer"
    url: "username.bsky.social"
    type: "bluesky"
    limit: 20
```

**Finding Bluesky handles:**
1. Visit a profile on https://bsky.app/
2. The URL will be: `https://bsky.app/profile/{handle}`
3. Use the `{handle}` as the `url` field

**Features:**
- Fetches public posts without authentication
- Converts posts to Article objects for integration with other sources
- Posts appear in chronological order
- Full post text included in summary
- Links back to original posts on bsky.app

**Requirements:**
The `atproto>=0.0.55` package is included in `requirements.txt` and handles all Bluesky API communication.

### 5. Enhanced Markdown Formatting

The agent prompt now includes explicit instructions about markdown formatting:

**Enforced format:**
- `# Daily Briefing - YYYY-MM-DD` for main title
- `## Theme Name` for each section/theme
- `**[Title](url)**` for article links
- `>` for blockquotes

This ensures consistent rendering in HTML emails.

## Complete Example

```python
from agent_briefing import AgentBriefing

# Create briefing system (automatically loads preferences)
briefing = AgentBriefing()

# Generate briefing with all features enabled
result = briefing.generate_briefing(
    days=1,
    use_enhanced_prompting=True
)

# Features automatically applied based on preferences.yaml:
# - Focus areas prioritized
# - Wikipedia context added where helpful
# - Research papers ranked with hybrid algorithm
# - Proper markdown formatting enforced

print(result)
```

## Customization Tips

### For News Junkies
```yaml
focus_areas:
  - Breaking news
  - Politics
  - International affairs
content_preferences:
  max_articles_per_section: 10  # More articles
  include_wikipedia_context: true  # More context
```

### For Researchers
```yaml
focus_areas:
  - AI research
  - Machine learning
  - Computer science
content_preferences:
  hybrid_research_ranking: true
research_preferences:
  max_research_papers: 20  # More papers
  research_categories:
    - cs.AI
    - cs.LG
    - cs.CL
```

### For Busy Executives
```yaml
focus_areas:
  - Business
  - Technology strategy
  - Market trends
exclude_topics:
  - Sports
  - Entertainment
content_preferences:
  max_articles_per_section: 3  # Concise
  include_wikipedia_context: false  # Skip context
```

## Technical Details

### Wikipedia API
- Uses Wikipedia REST API v1
- Returns summaries (configurable sentence count)
- Falls back gracefully if article not found
- Timeout: 5 seconds

### Preferences Loading
- Looks for `preferences.yaml` in current directory
- Uses safe YAML loading
- Merges with sensible defaults
- Graceful fallback if file missing

### Research Ranking Algorithm
- Uses same `rank_items()` method as original constrained approach
- Prompt focuses on: novelty, impact, clarity, relevance
- Returns top-K papers based on LLM scoring
- Falls back to first K papers if ranking fails

## Migration Guide

If you're upgrading from the basic agent-centric system:

1. **No breaking changes** - all features are opt-in
2. **Preferences are optional** - system works without preferences.yaml
3. **Wikipedia is optional** - agent only uses if helpful
4. **Hybrid ranking is opt-in** - enable via preferences

Simply start using the enhanced version and gradually adopt features as needed.

## Performance Notes

- **Wikipedia lookups**: ~100-200ms per lookup (agent decides when to use)
- **Research ranking**: Adds one LLM call per research source (~2-5 seconds)
- **Preferences loading**: <10ms at startup
- **Overall impact**: Minimal (~5-10% slower with all features enabled)

## Future Enhancements

Potential additions for future versions:
- More context sources (e.g., company databases, technical documentation)
- Dynamic preference learning (system learns your interests)
- Multi-language support
- Collaborative filtering (learn from similar users)
- Time-based preferences (different focus during weekdays vs weekends)

## Troubleshooting

**Preferences not loading:**
- Check file is named exactly `preferences.yaml`
- Verify YAML syntax (use a validator)
- Check file permissions

**Wikipedia context not appearing:**
- Ensure `include_wikipedia_context: true` in preferences
- Agent decides when context is helpful (not forced)
- Check internet connectivity

**Research ranking not working:**
- Verify `hybrid_research_ranking: true` in preferences
- Check research source names match (e.g., "ArXiv")
- Ensure Copilot CLI is working (used for ranking)

## Support

For issues or questions:
1. Check this guide
2. Review `preferences.yaml.example`
3. Check agent_briefing.py documentation
4. Open an issue on GitHub
