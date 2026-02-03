import feeds
from claude import Claude
import json
import re


class ResearchRanker:
    """
    Base class for research paper ranking strategies.
    Each ranker implements a different approach to selecting top papers.
    """
    
    def __init__(self, name, description, claude=None):
        self.name = name
        self.description = description
        self.claude = claude or Claude()
    
    def rank(self, articles, target=5):
        """Rank and select top articles. Override in subclasses."""
        raise NotImplementedError


class RelevanceRanker(ResearchRanker):
    """
    Ranks papers based on relevance to specific technical domains.
    Focuses on: distributed systems, performance, AI infrastructure, hardware.
    """
    
    def __init__(self, claude=None):
        super().__init__(
            name="🎯 Relevance Ranker",
            description="Prioritizes papers relevant to infrastructure, distributed systems, and AI hardware",
            claude=claude
        )
    
    def _rank_batch(self, articles, top_k=5):
        """Rank a batch of articles by relevance"""
        if len(articles) <= top_k:
            return articles
        
        article_list = []
        for i, article in enumerate(articles):
            article_list.append(
                f"[{i}] {article.title}\n"
                f"Summary: {article.summary[:200]}...\n"
                f"URL: {article.url}"
            )
        
        prompt = f"""You are reviewing {len(articles)} research articles from arXiv.
Select the TOP {top_k} papers most relevant to:
- Distributed systems and large-scale computing
- AI/ML infrastructure and training at scale
- Computer architecture and hardware design
- Performance optimization and systems research

Articles to review:
{''.join(article_list)}

Respond with ONLY a JSON array of the {top_k} indices (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array."""
        
        response = self.claude.generate(prompt)
        
        try:
            match = re.search(r'\[[\d,\s]+\]', response)
            if match:
                selected_indices = json.loads(match.group())
                return [articles[i] for i in selected_indices if i < len(articles)][:top_k]
        except Exception as e:
            print(f"RelevanceRanker parse error: {e}")
        
        return articles[:top_k]
    
    def rank(self, articles, target=5, batch_size=20):
        """Reduce articles through batched relevance ranking"""
        current = articles[:]
        
        while len(current) > target:
            batches = [current[i:i+batch_size] for i in range(0, len(current), batch_size)]
            reduced = []
            for batch in batches:
                top = self._rank_batch(batch, top_k=min(5, len(batch)))
                reduced.extend(top)
            
            if len(reduced) >= len(current):
                break
            current = reduced
        
        if len(current) > target:
            current = self._rank_batch(current, top_k=target)
        
        return current[:target]


class NoveltyImpactRanker(ResearchRanker):
    """
    Ranks papers based on novelty and potential real-world impact.
    Focuses on: breakthrough ideas, practical applications, industry relevance.
    """
    
    def __init__(self, claude=None):
        super().__init__(
            name="💡 Novelty & Impact Ranker",
            description="Prioritizes breakthrough ideas with potential real-world impact",
            claude=claude
        )
    
    def _rank_batch(self, articles, top_k=5):
        """Rank a batch of articles by novelty and impact"""
        if len(articles) <= top_k:
            return articles
        
        article_list = []
        for i, article in enumerate(articles):
            article_list.append(
                f"[{i}] {article.title}\n"
                f"Summary: {article.summary[:200]}...\n"
                f"URL: {article.url}"
            )
        
        prompt = f"""You are reviewing {len(articles)} research articles from arXiv.
Select the TOP {top_k} papers with the highest NOVELTY and POTENTIAL IMPACT:
- Breakthrough methodologies or surprising results
- Papers that could change how we think about a problem
- Practical applications with real-world potential
- Research that bridges theory and industry

Ignore incremental improvements. Prioritize bold, innovative ideas.

Articles to review:
{''.join(article_list)}

Respond with ONLY a JSON array of the {top_k} indices (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array."""
        
        response = self.claude.generate(prompt)
        
        try:
            match = re.search(r'\[[\d,\s]+\]', response)
            if match:
                selected_indices = json.loads(match.group())
                return [articles[i] for i in selected_indices if i < len(articles)][:top_k]
        except Exception as e:
            print(f"NoveltyImpactRanker parse error: {e}")
        
        return articles[:top_k]
    
    def rank(self, articles, target=5, batch_size=20):
        """Reduce articles through batched novelty/impact ranking"""
        current = articles[:]
        
        while len(current) > target:
            batches = [current[i:i+batch_size] for i in range(0, len(current), batch_size)]
            reduced = []
            for batch in batches:
                top = self._rank_batch(batch, top_k=min(5, len(batch)))
                reduced.extend(top)
            
            if len(reduced) >= len(current):
                break
            current = reduced
        
        if len(current) > target:
            current = self._rank_batch(current, top_k=target)
        
        return current[:target]


class Research:
    """Research paper aggregator with dual-ranker comparison"""
    
    def __init__(self, use_dual_ranker=True):
        self.articles = []
        self.claude = Claude()
        self.use_dual_ranker = use_dual_ranker
        
        # Initialize both rankers
        self.relevance_ranker = RelevanceRanker(claude=self.claude)
        self.novelty_ranker = NoveltyImpactRanker(claude=self.claude)

    def section_title(self):
        return "Arxiv Review"

    def _rank_and_select_top5(self, articles, batch_size=20):
        """Legacy method - use RelevanceRanker for backward compatibility"""
        return self.relevance_ranker._rank_batch(articles, top_k=5)

    def _reduce_articles(self, articles, target=5, batch_size=20):
        """Legacy method - use RelevanceRanker for backward compatibility"""
        return self.relevance_ranker.rank(articles, target=target, batch_size=batch_size)

    def pull_data(self, compare_rankers=None):
        """
        Pull and rank research articles.
        
        Args:
            compare_rankers: If True, use dual ranking comparison. 
                           If None, uses self.use_dual_ranker default.
        
        Returns:
            Formatted string of ranked articles, optionally with ranker comparison
        """
        if compare_rankers is None:
            compare_rankers = self.use_dual_ranker
            
        self.articles = feeds.Feeds.get_articles("https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR")
        
        if not compare_rankers:
            # Single ranker mode (backward compatible)
            self.articles = self._reduce_articles(self.articles, target=5, batch_size=20)
            formatted = "\n\n".join([xx.out_rich() for xx in self.articles])
            return formatted
        
        # Dual ranker comparison mode
        print(f"Running dual ranker comparison on {len(self.articles)} articles...")
        
        # Run both rankers
        print(f"  Running {self.relevance_ranker.name}...")
        relevance_picks = self.relevance_ranker.rank(self.articles[:], target=5)
        
        print(f"  Running {self.novelty_ranker.name}...")
        novelty_picks = self.novelty_ranker.rank(self.articles[:], target=5)
        
        # Find common picks (agreement between rankers)
        relevance_urls = {a.url for a in relevance_picks}
        novelty_urls = {a.url for a in novelty_picks}
        common_urls = relevance_urls & novelty_urls
        
        # Format output with comparison
        output = []
        
        # Agreement section - papers both rankers selected
        if common_urls:
            output.append("### 🤝 Both Rankers Agree On:")
            common_articles = [a for a in relevance_picks if a.url in common_urls]
            for article in common_articles:
                output.append(f"- **[{article.title}]({article.url})**")
                output.append(f"  - {article.summary[:150]}...")
            output.append("")
        
        # Relevance-only picks
        relevance_only = [a for a in relevance_picks if a.url not in common_urls]
        if relevance_only:
            output.append(f"### {self.relevance_ranker.name} Also Picks:")
            output.append(f"*{self.relevance_ranker.description}*")
            for article in relevance_only:
                output.append(f"- **[{article.title}]({article.url})**")
            output.append("")
        
        # Novelty-only picks
        novelty_only = [a for a in novelty_picks if a.url not in common_urls]
        if novelty_only:
            output.append(f"### {self.novelty_ranker.name} Also Picks:")
            output.append(f"*{self.novelty_ranker.description}*")
            for article in novelty_only:
                output.append(f"- **[{article.title}]({article.url})**")
            output.append("")
        
        # Store combined unique articles (deduplicate while preserving order)
        seen = set()
        unique_articles = []
        for a in relevance_picks + novelty_picks:
            if a.url not in seen:
                seen.add(a.url)
                unique_articles.append(a)
        self.articles = unique_articles
        
        return "\n".join(output)
    
    def pull_data_raw(self):
        """Pull raw article data for external processing"""
        self.articles = feeds.Feeds.get_articles("https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR")
        return self.articles

    def get_ranker_comparison_summary(self):
        """Get a summary comparing the two rankers' selections"""
        if not self.articles:
            self.pull_data(compare_rankers=True)
        
        relevance_picks = self.relevance_ranker.rank(self.articles[:], target=5)
        novelty_picks = self.novelty_ranker.rank(self.articles[:], target=5)
        
        relevance_urls = {a.url for a in relevance_picks}
        novelty_urls = {a.url for a in novelty_picks}
        
        agreement = len(relevance_urls & novelty_urls)
        
        return {
            'relevance_count': len(relevance_picks),
            'novelty_count': len(novelty_picks),
            'agreement_count': agreement,
            'agreement_pct': agreement / 5 * 100 if len(relevance_picks) else 0
        }


if __name__ == "__main__":
    print("Loading Research module with dual rankers...")
    xx = Research(use_dual_ranker=True)
    print("\n=== Pulling and ranking data ===\n")
    result = xx.pull_data(compare_rankers=True)
    print(result)

