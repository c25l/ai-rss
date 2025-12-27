import feeds
from ollama import Ollama

class Research:
    articles = []
    def __init__(self):
        self.articles = []
        self.ollama = Ollama()

    def section_title(self):
        return "Arxiv Review"

    def _rank_and_select_top5(self, articles, batch_size=20):
        """
        Use Claude to rank articles in a batch and select the top 5 most relevant/important.

        Args:
            articles: List of Article objects to rank
            batch_size: Number of articles in this batch

        Returns:
            List of top 5 articles selected by Claude
        """
        if len(articles) <= 5:
            return articles

        # Format articles for Claude to review
        article_list = []
        for i, article in enumerate(articles):
            article_list.append(
                f"[{i}] {article.title}\n"
                f"Summary: {article.summary[:200]}...\n"
                f"URL: {article.url}"
            )

        prompt = f"""You are reviewing {len(articles)} research articles from arXiv.
Please analyze these articles and select the TOP 5 most interesting, relevant, or impactful papers.
Focus on: novelty, potential impact, clarity of contribution, and relevance to distributed systems, performance, and computer architecture.

Articles to review:
{''.join([f'\n{a}\n' for a in article_list])}

Respond with ONLY a JSON array of the 5 indices you selected (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array."""

        response = self.ollama.generate(prompt)

        # Parse the response to get indices
        try:
            import json
            import re
            # Extract JSON array from response
            match = re.search(r'\[[\d,\s]+\]', response)
            if match:
                selected_indices = json.loads(match.group())
                # Return selected articles
                return [articles[i] for i in selected_indices if i < len(articles)]
        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            # Fallback to first 5
            return articles[:5]

        # Fallback to first 5
        return articles[:5]

    def _reduce_articles(self, articles, target=5, batch_size=20):
        """
        Recursively reduce articles by selecting top 5 from groups of 20 until only target remain.

        Args:
            articles: List of articles to reduce
            target: Target number of articles (default: 5)
            batch_size: Size of batches to process (default: 20)

        Returns:
            Reduced list of articles
        """
        current = articles[:]
        print(f"Reducing from {len(articles)} to {target} in batches of {batch_size}")
        while len(current) > target:
            # Split into batches of batch_size
            batches = [current[i:i+batch_size] for i in range(0, len(current), batch_size)]

            # Select top 5 from each batch using Claude
            reduced = []
            for batch in batches:
                top5 = self._rank_and_select_top5(batch, batch_size=len(batch))
                reduced.extend(top5)

            # If we didn't reduce (e.g., all batches had ≤5 items), break to avoid infinite loop
            if len(reduced) >= len(current):
                break

            current = reduced

        # Final selection if we still have more than target
        if len(current) > target:
            current = self._rank_and_select_top5(current, batch_size=len(current))

        return current[:target]

    def pull_data(self):
        self.articles = feeds.Feeds.get_articles("https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR")
        # Apply clever reduction: top 5 from groups of 20, recursively until only 5 remain
        self.articles = self._reduce_articles(self.articles, target=5, batch_size=20)

        # Format articles for output
        formatted = "\n\n".join([xx.out_rich() for xx in self.articles])
        return formatted
    
if __name__ == "__main__":
    print("loading object")
    xx = Research()
    print("pulling data")
    print(xx.pull_data())

