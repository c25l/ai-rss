#!/usr/bin/env python3
"""
Archive module for AIRSS Daily Briefings.

Saves briefings to JSON files organized by date for web viewing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from markdown import markdown


class Archiver:
    """Manages archiving of daily briefings to filesystem."""

    def __init__(self, archive_dir="/Media/source/airss/.archive"):
        """
        Initialize the Archiver.

        Args:
            archive_dir: Base directory for archives (default: /Media/source/airss/.archive)
        """
        self.archive_dir = Path(archive_dir)
        self.briefings_dir = self.archive_dir / "briefings"

    def save_briefing(self, content_markdown, subject, metadata=None):
        """
        Save a briefing to the archive.

        Args:
            content_markdown: Final polished markdown content
            subject: Email subject line
            metadata: Optional dict of additional metadata

        Returns:
            Path to saved file
        """
        # Create year/month subdirectories
        now = datetime.now()
        year_dir = self.briefings_dir / str(now.year)
        month_dir = year_dir / f"{now.month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename (using timestamp for uniqueness if multiple runs per day)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M")
        filename = f"{date_str}_{time_str}.json"
        filepath = month_dir / filename

        # Convert markdown to HTML
        content_html = markdown(content_markdown)

        # Build archive entry
        archive_entry = {
            "date": date_str,
            "subject": subject,
            "timestamp": now.isoformat(),
            "content_markdown": content_markdown,
            "content_html": content_html,
            "metadata": metadata or {}
        }

        # Save to JSON
        with open(filepath, 'w') as f:
            json.dump(archive_entry, f, indent=2)

        print(f"✓ Briefing archived: {filepath}")
        return filepath
