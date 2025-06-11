#!/usr/bin/env python3
"""
Complete Newsletter Generator for AIRSS
Takes all articles and generates integrated narratives and complete newsletter using AI
"""

import requests
import json
from datetime import datetime
from datamodel import Group, Article
from generate import generate

def create_narrative_prompt(group):
    """Create a prompt for generating an integrated narrative from related articles"""
    
    # Extract and organize article information by narrative themes
    articles_info = []
    sources = set()
    narrative_themes = set()
    
    for article in group.articles:
        sources.add(article.source)
        if hasattr(article, 'keywords') and article.keywords:
            narrative_themes.update(article.keywords)
            
        info = f"• {article.title} ({article.source})\n  {article.summary}"
        articles_info.append(info)
    
    articles_text = "\n".join(articles_info)
    themes_text = ", ".join(list(narrative_themes)[:3]) if narrative_themes else group.text
    
    prompt = f"""Write an integrated news narrative that weaves together the following related developments around {themes_text}. 

Create a cohesive story that:
- Identifies the central narrative thread connecting these articles
- Explains how the different developments relate to each other
- Provides context for why this story matters
- Incorporates key facts from multiple sources naturally
- Maintains journalistic objectivity

Related articles to integrate:
{articles_text}

Write the narrative as a compelling news story with a clear headline:"""
    
    return prompt

def generate_integrated_narrative(group):
    """Generate an integrated narrative that weaves together related articles"""
    
    if not group.articles or len(group.articles) == 0:
        return None
        
    # For single articles, enhance with context
    if len(group.articles) == 1:
        article = group.articles[0]
        narrative_context = ""
        if hasattr(article, 'keywords') and article.keywords:
            narrative_context = f" This development is part of broader trends in {', '.join(article.keywords[:2])}."
            
        return {
            'headline': article.title,
            'narrative': article.summary + narrative_context,
            'article_count': 1,
            'sources': [article.source],
            'urls': [article.url],
            'themes': getattr(article, 'keywords', [])
        }
    
    # For multiple articles, create integrated narrative
    prompt = create_narrative_prompt(group)
    
    try:
        narrative_text = generate(prompt)
        
        # Extract headline and narrative content
        lines = [line.strip() for line in narrative_text.strip().split('\n') if line.strip()]
        
        # Find headline (usually first substantial line)
        headline = lines[0] if lines else group.text
        narrative_start = 1
        
        # Clean up headline formatting
        if headline.startswith(('# ', '## ', '### ')):
            headline = headline.lstrip('# ')
        elif headline.startswith('**') and headline.endswith('**'):
            headline = headline[2:-2]
        elif headline.upper() == headline and len(headline) < 100:
            # If first line is all caps (title case), use it as headline
            pass
        else:
            # If first line doesn't look like a headline, use group text
            headline = group.text
            narrative_start = 0
            
        # Join remaining lines as narrative
        narrative = '\n\n'.join(lines[narrative_start:]) if len(lines) > narrative_start else narrative_text
        
        # Extract themes from articles
        all_themes = set()
        for article in group.articles:
            if hasattr(article, 'keywords'):
                all_themes.update(article.keywords)
        
        return {
            'headline': headline,
            'narrative': narrative or "Multiple related developments continue to unfold.",
            'article_count': len(group.articles),
            'sources': list(set([a.source for a in group.articles])),
            'urls': [a.url for a in group.articles],
            'themes': list(all_themes)
        }
        
    except Exception as e:
        print(f"Error generating narrative for group '{group.text}': {e}")
        # Fallback to thematic summary
        themes = set()
        for article in group.articles:
            if hasattr(article, 'keywords'):
                themes.update(article.keywords)
        
        fallback_narrative = f"Multiple interconnected developments around {', '.join(list(themes)[:2]) if themes else 'this topic'}. "
        fallback_narrative += f"Key stories include: {'; '.join([a.title for a in group.articles[:3]])}."
        
        return {
            'headline': group.text,
            'narrative': fallback_narrative,
            'article_count': len(group.articles),
            'sources': list(set([a.source for a in group.articles])),
            'urls': [a.url for a in group.articles],
            'themes': list(themes)
        }

def format_narrative_html(narrative_data):
    """Format an integrated narrative as HTML for email"""
    
    sources_text = ", ".join(narrative_data['sources'])
    
    # Create embedded links within the narrative text
    narrative_with_links = narrative_data.get('narrative', narrative_data.get('story', ''))
    
    # Add reference links at the end
    reference_links = "<br><small><strong>Sources:</strong> " + " | ".join([
        f"<a href='{url}' style='color: #007acc; text-decoration: none;'>[{i+1}]</a>" 
        for i, url in enumerate(narrative_data['urls'])
    ]) + "</small>"
    
    # Add theme tags if available
    theme_tags = ""
    if 'themes' in narrative_data and narrative_data['themes']:
        theme_tags = "<br><small><strong>Topics:</strong> " + ", ".join(narrative_data['themes'][:4]) + "</small>"
    
    return f"""
<div style="margin-bottom: 30px; border-left: 4px solid #28a745; padding-left: 20px; background-color: #f8fff9; padding: 20px;">
    <h2 style="margin: 0 0 15px 0; color: #28a745; font-size: 20px; font-weight: 600;">{narrative_data['headline']}</h2>
    <div style="margin: 0 0 20px 0; line-height: 1.7; color: #2c3e50; font-size: 15px;">
        {narrative_with_links}
    </div>
    <div style="color: #6c757d; font-size: 13px; border-top: 1px solid #e9ecef; padding-top: 10px;">
        <strong>{narrative_data['article_count']}</strong> article{'s' if narrative_data['article_count'] > 1 else ''} from <strong>{sources_text}</strong>
        {reference_links}
        {theme_tags}
    </div>
</div>
"""

def format_story_markdown(story_data):
    """Format a story as Markdown"""
    
    sources_text = ", ".join(story_data['sources'])
    
    links_section = ""
    if len(story_data['urls']) > 1:
        links_section = "\n\n**Sources:** " + " | ".join([
            f"[Link {i+1}]({url})" 
            for i, url in enumerate(story_data['urls'][:5])
        ])
    elif len(story_data['urls']) == 1:
        links_section = f"\n\n[Read more]({story_data['urls'][0]})"
    
    return f"""## {story_data['headline']}

{story_data['story']}

*{story_data['article_count']} article{'s' if story_data['article_count'] > 1 else ''} • {sources_text}*{links_section}

---
"""

def generate_news_digest(groups):
    """Generate integrated narrative digest from article groups"""
    
    narratives = []
    
    # Sort groups by article count (prioritize larger narratives)
    sorted_groups = sorted(groups.values(), key=lambda g: len(g.articles), reverse=True)
    
    for group in sorted_groups:
        if group.text == "Misc." or len(group.articles) == 0:
            continue  # Skip misc or empty groups
            
        narrative = generate_integrated_narrative(group)
        if narrative:
            narratives.append(narrative)
    
    return narratives

def create_email_content(narratives):
    """Create HTML email content from integrated narratives"""
    
    narrative_html = "".join([format_narrative_html(narrative) for narrative in narratives])
    
    total_articles = sum(n.get('article_count', 0) for n in narratives)
    unique_sources = set()
    all_themes = set()
    
    for narrative in narratives:
        unique_sources.update(narrative.get('sources', []))
        all_themes.update(narrative.get('themes', []))
    
    # Create summary statistics
    stats_html = f"""
    <div style="background-color: #f1f3f4; padding: 15px; margin-bottom: 30px; border-radius: 5px;">
        <h3 style="margin: 0 0 10px 0; color: #5f6368; font-size: 16px;">Today's Intelligence Brief</h3>
        <p style="margin: 0; color: #5f6368; font-size: 14px;">
            <strong>{len(narratives)}</strong> integrated narratives from <strong>{total_articles}</strong> articles 
            across <strong>{len(unique_sources)}</strong> sources
        </p>
        <p style="margin: 5px 0 0 0; color: #5f6368; font-size: 13px;">
            <strong>Key themes:</strong> {', '.join(list(all_themes)[:8])}
        </p>
    </div>
    """
    
    html_content = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>AI-Generated News Intelligence Brief</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fafafa;">
    <h1 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 15px; margin-bottom: 20px;">
        📰 News Intelligence Brief
    </h1>
    <p style="color: #5f6368; font-size: 16px; margin-bottom: 5px;">
        {datetime.now().strftime('%A, %B %d, %Y')}
    </p>
    
    {stats_html}
    
    {narrative_html}
    
    <hr style="margin: 40px 0 20px 0; border: none; border-top: 1px solid #dadce0;">
    <p style="color: #9aa0a6; font-size: 12px; text-align: center;">
        Generated by AIRSS Intelligence System • {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
    </p>
</body>
</html>
"""
    
    return html_content

def generate_complete_newsletter(articles):
    """Generate complete newsletter from all articles using AI to group and create narratives"""
    
    # Select diverse articles from different sources, prioritizing major news sources
    priority_sources = ['NYT World', 'NYT US', 'NYT Sci.', 'The Atlantic', 'Ars Technica', 'Wired Sci.', 'Wired Ai.', 'Vox']
    
    selected_articles = []
    sources_used = set()
    
    # First pass: get articles from priority sources
    for article in articles:
        if article.source in priority_sources and article.source not in sources_used:
            selected_articles.append(article)
            sources_used.add(article.source)
            if len(selected_articles) >= 15:
                break
    
    # Second pass: fill remaining slots with diverse sources
    for article in articles:
        if len(selected_articles) >= 40:
            break
        if article.source not in sources_used:
            selected_articles.append(article)
            sources_used.add(article.source)
    
    # Third pass: add more from any source if needed
    for article in articles:
        if len(selected_articles) >= 40:
            break
        if article not in selected_articles:
            selected_articles.append(article)
    
    limited_articles = selected_articles[:40]
    
    # Prepare articles for AI processing with concise format
    articles_text = []
    for i, article in enumerate(limited_articles):
        article_info = f"{i+1}. {article.title} ({article.source})\n   {article.summary}\n   {article.url}"
        articles_text.append(article_info)
    
    all_articles_text = "\n\n".join(articles_text)
    
    # Create explicit HTML prompt
    newsletter_prompt = f"""Create an HTML newsletter from these {len(limited_articles)} articles. Group related stories into narrative sections.

ARTICLES:
{all_articles_text}

OUTPUT: HTML only. Start with <h2>Section Title</h2> then <p>narrative content with <a href="url">source links</a></p>. Create 6-8 sections. Example:

<h2>Technology Developments</h2>
<p>Major tech companies continue advancing AI capabilities. <a href="url1">Company A announced</a> new features while <a href="url2">researchers reported</a> breakthrough findings.</p>

<h2>Global Politics</h2>  
<p>International relations evolve as <a href="url3">leaders meet</a> to discuss ongoing challenges.</p>"""

    try:
        print(f"Generating newsletter from {len(limited_articles)} articles...")
        newsletter_content = generate(newsletter_prompt)
        
        print(f"AI generated {len(newsletter_content)} characters")
        print(f"First 300 chars: {newsletter_content[:300]}...")
        
        if not newsletter_content or len(newsletter_content.strip()) < 100:
            print("AI generation failed or returned minimal content, using fallback")
            raise Exception("Minimal content returned")
        
        # Clean up the content - remove any markdown artifacts
        cleaned_content = newsletter_content.strip()
        if cleaned_content.startswith('```html'):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()
        
        # Ensure we have HTML tags
        if not ('<h2>' in cleaned_content or '<h1>' in cleaned_content):
            print("Generated content lacks HTML structure, using fallback")
            raise Exception("No HTML structure found")
        
        # Wrap in complete HTML structure
        newsletter_html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>AI News Intelligence Brief</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fafafa; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 15px; margin-bottom: 20px; }}
        h2 {{ color: #34a853; margin-top: 30px; margin-bottom: 15px; font-size: 20px; }}
        p {{ line-height: 1.6; margin-bottom: 15px; color: #333; }}
        a {{ color: #1a73e8; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .section {{ margin-bottom: 25px; }}
    </style>
</head>
<body>
    <h1>📰 News Intelligence Brief - {datetime.now().strftime('%B %d, %Y')}</h1>
    <p style="color: #666; font-style: italic;">Integrated narratives from {len(limited_articles)} articles across {len(sources_used)} sources</p>
    
    {cleaned_content}
    
    <hr style="margin: 40px 0 20px 0; border: none; border-top: 1px solid #dadce0;">
    <p style="color: #9aa0a6; font-size: 12px; text-align: center;">
        Generated by AIRSS Intelligence System • {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
    </p>
</body>
</html>
"""
        
        return newsletter_html
        
    except Exception as e:
        print(f"Error generating newsletter: {e}")
        # Enhanced fallback with better formatting
        fallback_stories = []
        for article in limited_articles[:10]:
            fallback_stories.append(f"""
            <div style="margin-bottom: 20px; padding: 15px; border-left: 3px solid #1a73e8; background-color: white;">
                <h3 style="margin: 0 0 10px 0;"><a href="{article.url}" style="color: #1a73e8; text-decoration: none;">{article.title}</a></h3>
                <p style="margin: 0 0 10px 0; color: #333;">{article.summary}</p>
                <small style="color: #666;">Source: {article.source}</small>
            </div>
            """)
        
        fallback_html = f"""
<html>
<head>
    <meta charset="utf-8">
    <title>News Brief - {datetime.now().strftime('%Y-%m-%d')}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fafafa;">
    <h1 style="color: #1a73e8;">Today's News - {datetime.now().strftime('%B %d, %Y')}</h1>
    <p style="color: #666;">Top stories from {len(articles)} articles</p>
    
    {''.join(fallback_stories)}
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #999; font-size: 12px; text-align: center;"><em>Generated by AIRSS</em></p>
</body>
</html>
"""
        return fallback_html