import os
import re
from datetime import datetime, timedelta
from pathlib import Path


class Journal(object):
    def __init__(self):
        self.entries = []
        self.obsidian_dir = "/home/chris/Downloads/obsidian/config/ChoicesScaffold/"
        self.journal_dir = os.path.join(self.obsidian_dir, "Journal/Day")

    def section_title(self):
        return "Journal Entries"

    def clean_content(self, text):
        """
        Clean Obsidian-specific markup from text:
        - Remove wikilinks [[...]]
        - Remove transclusions ![[...]]
        - Remove dataview code blocks
        """
        # Remove dataview code blocks (```dataview ... ```)
        text = re.sub(r'```dataview.*?```', '', text, flags=re.DOTALL)

        # Remove transclusions ![[...]]
        text = re.sub(r'!\[\[.*?\]\]', '', text)

        # Remove wikilinks [[link|display]] -> display
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)

        # Remove simple wikilinks [[link]] -> link
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)

        return text

    def get_recent_files(self, days=7):
        """
        Get journal files from the last N days.
        Returns list of (filename, filepath) tuples, sorted newest first.
        """
        if not os.path.exists(self.journal_dir):
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        files = []

        for filename in os.listdir(self.journal_dir):
            if not filename.endswith(".md"):
                continue

            # Extract date from filename (format: YYYY-MM-DD.md)
            try:
                date_str = filename.replace(".md", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date >= cutoff_date:
                    filepath = os.path.join(self.journal_dir, filename)
                    files.append((filename, filepath, file_date))
            except ValueError:
                # Skip files that don't match the date format
                continue

        # Sort by date, newest first
        files.sort(key=lambda x: x[2], reverse=True)
        return [(f[0], f[1]) for f in files]

    def search_entries(self, search_term, days=30):
        """
        Search journal entries for a specific term.
        Returns list of matching entries with context.
        """
        results = []
        files = self.get_recent_files(days=days)

        for filename, filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    cleaned_content = self.clean_content(content)

                    # Case-insensitive search
                    if search_term.lower() in cleaned_content.lower():
                        results.append({
                            "date": filename.replace(".md", ""),
                            "filepath": filepath,
                            "content": cleaned_content
                        })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

        return results

    def pull_data(self, rawmode=False, days=7):
        """
        Pull journal entries from the last N days.
        Extracts open tasks and recent content.
        """
        document = {}
        files = self.get_recent_files(days=days)

        if not files:
            self.entries = ["No journal entries found."]
            return self.entries

        recent = []
        tasks = []

        for filename, filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    cleaned = self.clean_content(content)
                    lines = cleaned.split("\n")

                    # Add header with date
                    recent.append(f"\n## {filename.replace('.md', '')}")

                    # Extract tasks and content
                    for line in lines:
                        stripped = line.strip()

                        # Collect open tasks
                        if stripped.startswith("- [ ] "):
                            tasks.append(f"{stripped} (from {filename.replace('.md', '')})")

                        # Add non-empty lines to recent content
                        if stripped:
                            recent.append(line)

            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

        self.entries = ["# Open Tasks", ""] + tasks + ["", "# Recent Journal Entries"] + recent
        return self.entries

    def output(self):
        """Return formatted journal entries."""
        if not self.entries:
            return "No journal entries found."
        return "\n".join(self.entries)
