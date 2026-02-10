#!/usr/bin/env python
"""
Static Site Publisher for H3lPeR

Generates a static site from briefing JSON files and publishes to a local
clone of tumble-dry-low.github.io. Designed to be called after daily briefing generation.

Usage:
    python publish_site.py                    # generate + git push
    python publish_site.py --no-push          # generate only, skip git push
    python publish_site.py --site-dir /path   # specify site directory

Environment:
    GITHUB_PAGES_DIR  — path to local clone of tumble-dry-low.github.io
"""

import argparse
import html as html_mod
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

# Ensure H3lPeR modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from emailer import render_briefing_content, validate_briefing_json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BRIEFINGS_DIR = os.path.join(PROJECT_ROOT, "briefings")
WEB_PUBLIC_DIR = os.path.join(PROJECT_ROOT, "web", "public")


# =============================================================================
# Preferences
# =============================================================================

def _load_preferences():
    """Load preferences.yaml if available."""
    try:
        import yaml
        pref_path = os.path.join(PROJECT_ROOT, "preferences.yaml")
        if os.path.exists(pref_path):
            with open(pref_path, "r") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}


# =============================================================================
# Templates
# =============================================================================

def _page_wrapper(title, body, active_page=""):
    """Wrap body HTML in the full page chrome (Pico CSS, nav, footer)."""
    def _nav_class(page):
        return ' class="active"' if page == active_page else ""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_mod.escape(title)} — H3lPeR</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="/css/style.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
</head>
<body>
  <nav class="container-fluid">
    <ul>
      <li><strong>H3lPeR</strong></li>
    </ul>
    <ul>
      <li><a href="/"{_nav_class("home")}>Latest</a></li>
      <li><a href="/dashboard/"{_nav_class("dashboard")}>Dashboard</a></li>
      <li><a href="/citations/"{_nav_class("citations")}>Citations</a></li>
      <li><a href="/briefings/"{_nav_class("briefings")}>Archive</a></li>
    </ul>
  </nav>
  <main class="container">
{body}
  </main>
  <footer class="container">
    <small>H3lPeR — Personal Briefing System</small>
  </footer>
  <script src="/js/app.js"></script>
</body>
</html>"""


def _dashboard_page(stock_symbols):
    """Generate dashboard body HTML."""
    symbols_json = json.dumps([{"s": s} for s in stock_symbols])
    tv_config = json.dumps({
        "colorTheme": "light",
        "dateRange": "1D",
        "showChart": True,
        "locale": "en",
        "largeChartUrl": "",
        "isTransparent": True,
        "showSymbolLogo": True,
        "showFloatingTooltip": False,
        "width": "100%",
        "height": "450",
        "tabs": [{
            "title": "Watchlist",
            "symbols": [{"s": s} for s in stock_symbols],
            "originalTitle": "Watchlist",
        }],
    })

    body = f"""
<h1>Dashboard</h1>

<article>
  <header>🌤️ Weather Forecast</header>
  <div id="weather-alerts"></div>
  <div class="chart-container">
    <canvas id="weather-chart"></canvas>
  </div>
</article>

<article>
  <header>☀️ Space Weather — Kp Index (Observed + Forecast)</header>
  <div class="chart-container chart-compact">
    <canvas id="kp-chart"></canvas>
  </div>
  <small class="swpc-credit">
    Data: <a href="https://www.swpc.noaa.gov" target="_blank">NOAA SWPC</a> · Kp ≥ 5 = geomagnetic storm
  </small>
</article>

<article>
  <header>📈 Markets</header>
  <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
    {tv_config}
    </script>
  </div>
</article>

<script src="/js/weather.js"></script>
<script src="/js/spaceweather.js"></script>
"""
    return body


def _citations_page():
    """Generate citations page body HTML showing top cited papers."""
    # Load citation data
    from citations_data import load_citation_data
    citation_data = load_citation_data()
    
    if not citation_data or not citation_data.get('papers'):
        body = """
<h1>📊 Most Cited Papers</h1>
<article>
  <p><em>No citation data available yet. Citation analysis will run during the next daily briefing.</em></p>
</article>
"""
        return body
    
    # Extract metadata
    generated_at = citation_data.get('generated_at', 'Unknown')
    params = citation_data.get('analysis_params', {})
    days = params.get('days', 1)
    papers = citation_data.get('papers', [])
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(generated_at)
        timestamp_str = dt.strftime('%B %d, %Y at %I:%M %p UTC')
    except:
        timestamp_str = generated_at
    
    # Build papers HTML
    papers_html = []
    for i, paper in enumerate(papers, 1):
        title = html_mod.escape(paper.get('title', 'Untitled'))
        url = html_mod.escape(paper.get('url', '#'))
        summary = html_mod.escape(paper.get('summary', '')[:400])
        if len(paper.get('summary', '')) > 400:
            summary += "..."
        
        cite_count = paper.get('citation_count', 0)
        total_citations = paper.get('total_citations', 0)
        
        paper_html = f"""
<article>
  <h3>{i}. <a href="{url}" target="_blank">{title}</a></h3>
  <p>
    <strong>📊 Cited by recent papers:</strong> {cite_count} times<br>
    <strong>📚 Total citations:</strong> {total_citations:,}
  </p>
  <p><small>{summary}</small></p>
</article>
"""
        papers_html.append(paper_html)
    
    papers_section = "\n".join(papers_html)
    
    body = f"""
<h1>📊 Most Cited Papers</h1>
<p>
  <em>Papers most frequently cited by recent arXiv submissions.</em><br>
  <small>Last updated: {timestamp_str} | Analyzing papers from last {days} day(s)</small>
</p>

{papers_section}
"""
    return body


def _model_pill(model_name):
    """Render a small pill badge for the model name."""
    if not model_name:
        return ""
    escaped = html_mod.escape(str(model_name))
    return (
        f'<span style="display:inline-block;background-color:#7f8c8d;color:#fff;'
        f'font-size:10px;font-weight:600;padding:1px 7px;border-radius:9px;'
        f'vertical-align:middle;margin-left:6px;">{escaped}</span>'
    )


def _briefings_archive_page(briefings):
    """Generate briefings archive list body HTML.

    briefings: list of dicts with keys: filename, date_str, title, section_count, model
    """
    if not briefings:
        items = "  <li><em>No briefings found</em></li>"
    else:
        lines = []
        for b in briefings:
            html_file = b["html_filename"]
            model = _model_pill(b.get("model", ""))
            lines.append(
                f'  <li><a href="/briefings/{html_mod.escape(html_file)}">'
                f'<strong>{html_mod.escape(b["date_str"])}</strong>'
                f'<small>{html_mod.escape(b["title"])} · {b["section_count"]} sections{model}</small>'
                f'</a></li>'
            )
        items = "\n".join(lines)

    body = f"""
<h1>Briefings</h1>
<ul id="briefing-list">
{items}
</ul>
"""
    return body


def _briefing_page(briefing_content_html, title, date_str, model=None):
    """Generate individual briefing page body HTML."""
    model_html = _model_pill(model) if model else ""
    body = f"""
<h1>{html_mod.escape(title)} {model_html}</h1>
<p><a href="/briefings/">← Back to all briefings</a></p>
<div id="briefing-content">
  {briefing_content_html}
</div>
"""
    return body


# =============================================================================
# Briefing discovery
# =============================================================================

def _discover_briefings():
    """Scan briefings/ directory, return list of briefing metadata sorted newest-first.

    Every JSON file becomes its own page, using the original filename stem
    (e.g. 260207-a64a7c51426d.json → 260207-a64a7c51426d.html).
    """
    if not os.path.isdir(BRIEFINGS_DIR):
        return []

    files = [f for f in os.listdir(BRIEFINGS_DIR) if f.endswith(".json")]
    if not files:
        return []

    entries = []
    for fname in files:
        fpath = os.path.join(BRIEFINGS_DIR, fname)
        match = re.match(r"^(\d{6})-", fname)
        if not match:
            continue
        yy, mm, dd = match.group(1)[:2], match.group(1)[2:4], match.group(1)[4:6]
        date_str = f"20{yy}-{mm}-{dd}"
        stem = fname.rsplit(".", 1)[0]  # e.g. "260207-a64a7c51426d"

        try:
            with open(fpath, "r") as f:
                doc = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        entries.append({
            "json_filename": fname,
            "json_path": fpath,
            "date_str": date_str,
            "date_sort": f"20{yy}{mm}{dd}",
            "html_filename": f"{stem}.html",
            "title": doc.get("title", "Untitled Briefing"),
            "section_count": len(doc.get("children", [])),
            "model": doc.get("model"),
            "doc": doc,
            "mtime": os.path.getmtime(fpath),
        })

    # Sort newest-first by date, then by mtime within same date
    entries.sort(key=lambda e: (e["date_sort"], e["mtime"]), reverse=True)
    return entries


# =============================================================================
# Static asset copying
# =============================================================================

def _copy_static_assets(site_dir):
    """Copy CSS and JS files from web/public/ to the site directory."""
    for subdir in ("css", "js"):
        src = os.path.join(WEB_PUBLIC_DIR, subdir)
        dst = os.path.join(site_dir, subdir)
        if not os.path.isdir(src):
            continue
        os.makedirs(dst, exist_ok=True)
        for fname in os.listdir(src):
            src_file = os.path.join(src, fname)
            dst_file = os.path.join(dst, fname)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)


# =============================================================================
# Site generation
# =============================================================================

def generate_site(site_dir, incremental=True):
    """Generate the full static site into site_dir.

    Args:
        site_dir: Path to the local clone of tumble-dry-low.github.io
        incremental: If True, skip briefing HTML files that already exist
    """
    os.makedirs(site_dir, exist_ok=True)
    os.makedirs(os.path.join(site_dir, "briefings"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "dashboard"), exist_ok=True)

    prefs = _load_preferences()
    stock_symbols = prefs.get("stock_symbols", ["MSFT", "NVDA", "FOREXCOM:DJI", "FOREXCOM:SPX500"])

    # 1. Copy static assets
    _copy_static_assets(site_dir)
    print("✓ Static assets copied")

    # 2. Dashboard (/dashboard/index.html)
    dashboard_body = _dashboard_page(stock_symbols)
    dashboard_html = _page_wrapper("Dashboard", dashboard_body, active_page="dashboard")
    with open(os.path.join(site_dir, "dashboard", "index.html"), "w") as f:
        f.write(dashboard_html)
    print("✓ Dashboard generated")

    # 3. Citations page (/citations/index.html)
    os.makedirs(os.path.join(site_dir, "citations"), exist_ok=True)
    citations_body = _citations_page()
    citations_html = _page_wrapper("Most Cited Papers", citations_body, active_page="citations")
    with open(os.path.join(site_dir, "citations", "index.html"), "w") as f:
        f.write(citations_html)
    print("✓ Citations page generated")

    # 4. Discover and render briefings
    briefings = _discover_briefings()
    generated = 0
    skipped = 0

    for b in briefings:
        html_path = os.path.join(site_dir, "briefings", b["html_filename"])

        # Incremental: skip if HTML already exists and is newer than source JSON
        if incremental and os.path.exists(html_path):
            html_mtime = os.path.getmtime(html_path)
            if html_mtime >= b["mtime"]:
                skipped += 1
                continue

        try:
            validate_briefing_json(b["doc"])
            content_html = render_briefing_content(b["doc"])
        except Exception as e:
            print(f"  ⚠ Skipping {b['json_filename']}: {e}")
            continue

        body = _briefing_page(content_html, b["title"], b["date_str"], model=b.get("model"))
        page_html = _page_wrapper(b["title"], body, active_page="briefings")

        with open(html_path, "w") as f:
            f.write(page_html)
        generated += 1

    print(f"✓ Briefings: {generated} generated, {skipped} skipped (already exist)")

    # 5. Briefings archive page (always regenerated)
    archive_body = _briefings_archive_page(briefings)
    archive_html = _page_wrapper("Archive", archive_body, active_page="briefings")
    with open(os.path.join(site_dir, "briefings", "index.html"), "w") as f:
        f.write(archive_html)
    print(f"✓ Briefings archive ({len(briefings)} entries)")

    # 6. Landing page = latest briefing (always regenerated)
    if briefings:
        latest = briefings[0]
        try:
            validate_briefing_json(latest["doc"])
            content_html = render_briefing_content(latest["doc"])
            body = _briefing_page(content_html, latest["title"], latest["date_str"], model=latest.get("model"))
            landing_html = _page_wrapper(latest["title"], body, active_page="home")
            with open(os.path.join(site_dir, "index.html"), "w") as f:
                f.write(landing_html)
            print(f"✓ Landing page: {latest['date_str']}")
        except Exception as e:
            print(f"⚠ Could not generate landing page: {e}")
    else:
        # No briefings yet — show archive page as landing
        with open(os.path.join(site_dir, "index.html"), "w") as f:
            f.write(_page_wrapper("H3lPeR", archive_body, active_page="home"))

    # 7. .nojekyll to prevent GitHub Pages from processing with Jekyll
    nojekyll = os.path.join(site_dir, ".nojekyll")
    if not os.path.exists(nojekyll):
        with open(nojekyll, "w") as f:
            pass

    return len(briefings)


# =============================================================================
# Git automation
# =============================================================================

def git_publish(site_dir):
    """Commit and push changes in the site directory."""
    def _git(*args):
        result = subprocess.run(
            ["git"] + list(args),
            cwd=site_dir,
            capture_output=True,
            text=True,
        )
        return result

    # Check if it's a git repo
    r = _git("rev-parse", "--git-dir")
    if r.returncode != 0:
        print(f"⚠ {site_dir} is not a git repository — skipping publish")
        return False

    # Stage all changes
    _git("add", ".")

    # Check if there are changes to commit
    r = _git("diff", "--cached", "--quiet")
    if r.returncode == 0:
        print("✓ No changes to publish")
        return True

    # Commit
    today = datetime.now().strftime("%Y-%m-%d")
    r = _git("commit", "-m", f"Briefing {today}")
    if r.returncode != 0:
        print(f"⚠ Git commit failed: {r.stderr.strip()}")
        return False
    print(f"✓ Committed: Briefing {today}")

    # Push
    r = _git("push", "origin", "main")
    if r.returncode != 0:
        # Try 'master' branch as fallback
        r = _git("push", "origin", "master")
        if r.returncode != 0:
            print(f"⚠ Git push failed: {r.stderr.strip()}")
            return False
    print("✓ Pushed to GitHub Pages")
    return True


# =============================================================================
# Public API (for importing from daily_workflow_agent.py)
# =============================================================================

def publish_briefing(site_dir=None, push=True):
    """Generate the static site and optionally push to GitHub Pages.

    Args:
        site_dir: Path to local clone of tumble-dry-low.github.io (default: GITHUB_PAGES_DIR env var)
        push: Whether to git commit+push after generation

    Returns:
        True if successful
    """
    if site_dir is None:
        site_dir = os.environ.get("GITHUB_PAGES_DIR")
    if not site_dir:
        print("⚠ No site directory configured (set GITHUB_PAGES_DIR or pass --site-dir)")
        return False

    print(f"Publishing to {site_dir}")
    generate_site(site_dir, incremental=True)

    if push:
        return git_publish(site_dir)
    return True


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate and publish H3lPeR static site")
    parser.add_argument(
        "--site-dir",
        default=os.environ.get("GITHUB_PAGES_DIR"),
        help="Path to local clone of tumble-dry-low.github.io (default: $GITHUB_PAGES_DIR)",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Generate site but don't git commit/push",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Regenerate all briefing pages (disable incremental mode)",
    )
    args = parser.parse_args()

    if not args.site_dir:
        print("Error: specify --site-dir or set GITHUB_PAGES_DIR")
        sys.exit(1)

    print(f"Publishing to {args.site_dir}")
    generate_site(args.site_dir, incremental=not args.full)

    if not args.no_push:
        if not git_publish(args.site_dir):
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
