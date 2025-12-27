#!/usr/bin/env python3
"""
Caching module for AIRSS to eliminate redundant computations.

Caches:
1. Weather forecasts (1-hour TTL)
2. Calendar events (daily TTL - expires at midnight)
3. Tasks (daily TTL - expires at midnight)
4. Article embeddings (7-day rolling window)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class Cache:
    """File-based cache with TTL support"""

    def __init__(self, cache_dir="/Media/source/airss/.cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "articles").mkdir(exist_ok=True)

    # ========================================================================
    # WEATHER CACHE (1-hour TTL)
    # ========================================================================

    def get_weather(self):
        """
        Get cached weather forecast if available and < 1 hour old.

        Returns:
            list or None: Weather periods list, or None if cache miss
        """
        now = datetime.now()
        cache_key = now.strftime("%Y-%m-%d_%H")  # Hour-based buckets
        cache_file = self.cache_dir / f"weather_{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                print(f"✓ Weather cache HIT ({cache_key})")
                return data['periods']
            except Exception as e:
                print(f"Warning: Weather cache read failed: {e}")
                return None

        print(f"✗ Weather cache MISS ({cache_key})")
        return None

    def set_weather(self, periods):
        """
        Cache weather forecast periods.

        Args:
            periods: list of weather period dicts
        """
        now = datetime.now()
        cache_key = now.strftime("%Y-%m-%d_%H")
        cache_file = self.cache_dir / f"weather_{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump({'periods': periods, 'cached_at': now.isoformat()}, f, indent=2)
            print(f"✓ Weather cached ({cache_key})")

            # Cleanup old weather caches (> 2 hours old)
            self._cleanup_old_files(self.cache_dir, pattern="weather_*.json", hours=2)
        except Exception as e:
            print(f"Warning: Weather cache write failed: {e}")

    # ========================================================================
    # CALENDAR CACHE (Daily TTL - expires at midnight)
    # ========================================================================

    def get_calendar(self):
        """
        Get cached calendar events if from today.

        Returns:
            list or None: Calendar events list, or None if cache miss
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = self.cache_dir / f"calendar_{today}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                print(f"✓ Calendar cache HIT ({today})")
                # Deserialize datetime strings back to datetime objects
                return self._deserialize_events(data['events'])
            except Exception as e:
                print(f"Warning: Calendar cache read failed: {e}")
                return None

        print(f"✗ Calendar cache MISS ({today})")
        return None

    def set_calendar(self, events):
        """
        Cache calendar events for today.

        Args:
            events: list of calendar event dicts (with datetime objects)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = self.cache_dir / f"calendar_{today}.json"

        try:
            # Serialize datetime objects to ISO strings
            serialized = self._serialize_events(events)
            with open(cache_file, 'w') as f:
                json.dump({'events': serialized, 'cached_at': datetime.now().isoformat()}, f, indent=2)
            print(f"✓ Calendar cached ({today})")

            # Cleanup old calendar caches (> 1 day old)
            self._cleanup_old_files(self.cache_dir, pattern="calendar_*.json", days=1)
        except Exception as e:
            print(f"Warning: Calendar cache write failed: {e}")

    # ========================================================================
    # TASKS CACHE (Daily TTL - expires at midnight)
    # ========================================================================

    def get_tasks(self):
        """
        Get cached tasks if from today.

        Returns:
            list or None: Tasks list, or None if cache miss
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = self.cache_dir / f"tasks_{today}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                print(f"✓ Tasks cache HIT ({today})")
                # Deserialize datetime strings back to datetime objects
                return self._deserialize_tasks(data['tasks'])
            except Exception as e:
                print(f"Warning: Tasks cache read failed: {e}")
                return None

        print(f"✗ Tasks cache MISS ({today})")
        return None

    def set_tasks(self, tasks):
        """
        Cache tasks for today.

        Args:
            tasks: list of task dicts (with datetime objects)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = self.cache_dir / f"tasks_{today}.json"

        try:
            # Serialize datetime objects to ISO strings
            serialized = self._serialize_tasks(tasks)
            with open(cache_file, 'w') as f:
                json.dump({'tasks': serialized, 'cached_at': datetime.now().isoformat()}, f, indent=2)
            print(f"✓ Tasks cached ({today})")

            # Cleanup old task caches (> 1 day old)
            self._cleanup_old_files(self.cache_dir, pattern="tasks_*.json", days=1)
        except Exception as e:
            print(f"Warning: Tasks cache write failed: {e}")

    # ========================================================================
    # ARTICLE EMBEDDINGS CACHE (7-day rolling window)
    # ========================================================================

    def get_article_embedding(self, article_url):
        """
        Get cached embedding for a specific article URL.

        Args:
            article_url: URL of the article

        Returns:
            dict or None: Article data with embedding, or None if not cached
        """
        # Check last 7 days of caches
        for days_ago in range(7):
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            cache_file = self.cache_dir / "articles" / f"embeddings_{date}.jsonl"

            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        for line in f:
                            article = json.loads(line)
                            if article.get('url') == article_url:
                                return article
                except Exception as e:
                    print(f"Warning: Article cache read failed for {date}: {e}")

        return None

    def get_cached_articles(self, days=3):
        """
        Load all cached articles from the last N days.

        Args:
            days: Number of days to look back (default 3)

        Returns:
            dict: {url: article_data} mapping of all cached articles
        """
        cached = {}

        for days_ago in range(days):
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            cache_file = self.cache_dir / "articles" / f"embeddings_{date}.jsonl"

            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        for line in f:
                            article = json.loads(line)
                            url = article.get('url')
                            if url and url not in cached:  # First occurrence wins (most recent)
                                cached[url] = article
                except Exception as e:
                    print(f"Warning: Article cache read failed for {date}: {e}")

        if cached:
            print(f"✓ Loaded {len(cached)} cached articles from last {days} days")

        return cached

    def set_article_embeddings(self, articles):
        """
        Cache articles with their embeddings for today.

        Args:
            articles: list of Article objects with .url, .title, .summary, .vector attributes
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = self.cache_dir / "articles" / f"embeddings_{today}.jsonl"

        try:
            # Append mode - add new articles to today's cache
            new_count = 0
            with open(cache_file, 'a') as f:
                for article in articles:
                    if hasattr(article, 'vector') and article.vector is not None:
                        # Serialize article to JSON line
                        article_data = {
                            'url': article.url,
                            'title': article.title,
                            'summary': article.summary,
                            'source': article.source,
                            'published_at': article.published_at.isoformat() if hasattr(article.published_at, 'isoformat') else str(article.published_at),
                            'vector': article.vector.tolist() if hasattr(article.vector, 'tolist') else article.vector
                        }
                        f.write(json.dumps(article_data) + '\n')
                        new_count += 1

            if new_count > 0:
                print(f"✓ Cached {new_count} article embeddings ({today})")

            # Cleanup old embedding caches (> 7 days old)
            self._cleanup_old_files(self.cache_dir / "articles", pattern="embeddings_*.jsonl", days=7)
        except Exception as e:
            print(f"Warning: Article embeddings cache write failed: {e}")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _serialize_events(self, events):
        """Convert datetime objects to ISO strings in events"""
        serialized = []
        for event in events:
            event_copy = event.copy()
            if 'start' in event_copy and hasattr(event_copy['start'], 'isoformat'):
                event_copy['start'] = event_copy['start'].isoformat()
            if 'end' in event_copy and hasattr(event_copy['end'], 'isoformat'):
                event_copy['end'] = event_copy['end'].isoformat()
            serialized.append(event_copy)
        return serialized

    def _deserialize_events(self, events):
        """Convert ISO strings back to datetime objects in events"""
        from dateutil import parser
        deserialized = []
        for event in events:
            event_copy = event.copy()
            if 'start' in event_copy and isinstance(event_copy['start'], str):
                event_copy['start'] = parser.parse(event_copy['start'])
            if 'end' in event_copy and isinstance(event_copy['end'], str):
                event_copy['end'] = parser.parse(event_copy['end'])
            deserialized.append(event_copy)
        return deserialized

    def _serialize_tasks(self, tasks):
        """Convert datetime objects to ISO strings in tasks"""
        serialized = []
        for task in tasks:
            task_copy = task.copy()
            if 'due' in task_copy and task_copy['due'] and hasattr(task_copy['due'], 'isoformat'):
                task_copy['due'] = task_copy['due'].isoformat()
            if 'completed' in task_copy and task_copy['completed'] and hasattr(task_copy['completed'], 'isoformat'):
                task_copy['completed'] = task_copy['completed'].isoformat()
            serialized.append(task_copy)
        return serialized

    def _deserialize_tasks(self, tasks):
        """Convert ISO strings back to datetime objects in tasks"""
        from dateutil import parser
        deserialized = []
        for task in tasks:
            task_copy = task.copy()
            if 'due' in task_copy and task_copy['due'] and isinstance(task_copy['due'], str):
                task_copy['due'] = parser.parse(task_copy['due'])
            if 'completed' in task_copy and task_copy['completed'] and isinstance(task_copy['completed'], str):
                task_copy['completed'] = parser.parse(task_copy['completed'])
            deserialized.append(task_copy)
        return deserialized

    def _cleanup_old_files(self, directory, pattern, hours=None, days=None):
        """Remove cache files older than specified time"""
        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
        elif days:
            cutoff = datetime.now() - timedelta(days=days)
        else:
            return

        for file in Path(directory).glob(pattern):
            if file.stat().st_mtime < cutoff.timestamp():
                try:
                    file.unlink()
                except Exception:
                    pass


if __name__ == "__main__":
    # Test the cache module
    print("Testing Cache module...\n")

    cache = Cache()

    # Test weather cache
    print("=== Weather Cache Test ===")
    weather = cache.get_weather()
    if weather is None:
        print("Caching test weather data...")
        cache.set_weather([{'name': 'Today', 'temp': 55, 'desc': 'Sunny'}])
        weather = cache.get_weather()
    print(f"Weather data: {weather}\n")

    # Test calendar cache
    print("=== Calendar Cache Test ===")
    calendar = cache.get_calendar()
    if calendar is None:
        print("Caching test calendar data...")
        from datetime import datetime
        cache.set_calendar([{
            'title': 'Test Event',
            'start': datetime.now(),
            'end': datetime.now() + timedelta(hours=1)
        }])
        calendar = cache.get_calendar()
    print(f"Calendar events: {len(calendar) if calendar else 0}\n")

    # Test tasks cache
    print("=== Tasks Cache Test ===")
    tasks = cache.get_tasks()
    if tasks is None:
        print("Caching test task data...")
        cache.set_tasks([{
            'title': 'Test Task',
            'due': datetime.now() + timedelta(days=1),
            'notes': 'Test notes'
        }])
        tasks = cache.get_tasks()
    print(f"Tasks: {len(tasks) if tasks else 0}\n")

    print("✓ Cache module tests complete")
