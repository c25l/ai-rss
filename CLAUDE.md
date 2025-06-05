# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

**Main execution:**
```bash
python3 airss.py
# or via shell script:
./run-nb.sh
```

**Terminal interface:**
```bash
npm install  # Install wetty for web terminal
```

## Architecture Overview

AIRSS is an intelligent RSS feed aggregator that follows this data flow:

1. **Feed Collection** (`feeds.py`) - Fetches from 20+ RSS sources with 3 feed types:
   - Type 1: Standard RSS feeds (majority)
   - Type 2: Hacker News daily digest (special link extraction)
   - Type 3: TLDR newsletters (requires HTTP requests to extract content)

2. **Content Processing** (`airss.py`) - AI-powered clustering:
   - Embeds articles using local Ollama API (`nomic-embed-text` model)
   - Extracts keywords via semantic similarity to 100+ predefined tags
   - Performs two-level K-means clustering (content + keywords)
   - Groups articles by topic similarity

3. **Email Generation** - Converts clustered articles to HTML email digest

## Required Services

**Local Ollama API** (http://localhost:11434):
```bash
# Must have these models installed:
ollama pull nomic-embed-text  # For embeddings
ollama pull qwen3:0.6b       # For text generation (generate.py)
```

**PostgreSQL Database** with connection string:
```bash
export PGVECTOR_URL="postgresql://postgres:yourpassword@localhost:5432/rss"
# Default: postgresql://postgres:yourpassword@localhost:5432/rss
```

**Email Configuration** - Currently hardcoded in `airss.py:158`:
- Uses iCloud SMTP (smtp.mail.me.com:587)
- Sender: christopherpbonnell@icloud.com
- Password stored in code (security concern)

## Database Schema

Tables created by `database.py:setup_db()`:
- `feeds` - RSS feed configurations (type, source, url)
- `articles` - Article storage with keywords and grouping
- `secrets` - Encrypted configuration values
- `topics` - Topic categorization

## Key Integration Points

**Feed Processing** (`feeds.py:FEEDS`):
- 24-hour article window with deduplication by title
- Categories: Science, Technology, US News, World News, Local News
- Sources include NYT, Wired, Nature, Science, Ars Technica, Vox

**Clustering Logic** (`airss.py:cluster`):
- Uses 100+ predefined keyword tags for semantic matching
- Silhouette analysis for optimal K-means cluster count
- Combines title/summary clustering with keyword clustering

**Content Generation** (`generate.py`):
- Uses `qwen3:0.6b` model for text generation
- Includes thinking pattern with `\\no_think` prompt modifier