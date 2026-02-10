#!/usr/bin/env python
"""
Demo script for arXiv Citation Graph Analyzer

This script demonstrates the citation analysis feature with example output.
In a real environment with network access, it would fetch actual data from arXiv and Semantic Scholar.
"""

def print_demo_output():
    """Print example output showing what the analyzer produces"""
    
    # Demo configuration
    NUM_PAPERS = 47
    
    print("=" * 70)
    print("arXiv Citation Graph Analyzer - Demo Output")
    print("=" * 70)
    print()
    
    print("Configuration:")
    print("  - Categories: cs.AI, cs.LG, cs.CL")
    print("  - Days back: 1")
    print("  - Top N papers: 10")
    print("  - Min citations: 2")
    print()
    
    print("-" * 70)
    print("STEP 1: Fetching Recent Papers")
    print("-" * 70)
    print("Fetching arXiv papers from RSS: https://export.arxiv.org/rss/cs.AI+cs.LG+cs.CL")
    print(f"Fetched {NUM_PAPERS} papers from arXiv RSS feed")
    print()
    
    print("-" * 70)
    print("STEP 2: Building Citation Graph")
    print("-" * 70)
    print(f"Building citation graph for {NUM_PAPERS} papers...")
    print(f"  [1/{NUM_PAPERS}] Fetching references for 2402.12345...")
    print("    Found 23 arXiv references")
    print(f"  [2/{NUM_PAPERS}] Fetching references for 2402.12346...")
    print("    Found 18 arXiv references")
    print(f"  [3/{NUM_PAPERS}] Fetching references for 2402.12347...")
    print("    Found 31 arXiv references")
    print("  ...")
    print(f"  [{NUM_PAPERS}/{NUM_PAPERS}] Fetching references for 2402.12391...")
    print("    Found 15 arXiv references")
    print()
    print("Citation graph built: 342 unique cited papers")
    print()
    
    print("-" * 70)
    print("STEP 3: Results - Most Cited Papers")
    print("-" * 70)
    print()
    
    # Example results
    results = [
        {
            "rank": 1,
            "title": "Attention Is All You Need",
            "arxiv_id": "1706.03762",
            "cited_by_recent": 12,
            "total_citations": 75432,
            "summary": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms..."
        },
        {
            "rank": 2,
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "arxiv_id": "1810.04805",
            "cited_by_recent": 9,
            "total_citations": 42108,
            "summary": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers..."
        },
        {
            "rank": 3,
            "title": "Language Models are Few-Shot Learners",
            "arxiv_id": "2005.14165",
            "cited_by_recent": 8,
            "total_citations": 31892,
            "summary": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples..."
        },
        {
            "rank": 4,
            "title": "Deep Residual Learning for Image Recognition",
            "arxiv_id": "1512.03385",
            "cited_by_recent": 7,
            "total_citations": 89651,
            "summary": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions..."
        },
        {
            "rank": 5,
            "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
            "arxiv_id": "2010.11929",
            "cited_by_recent": 6,
            "total_citations": 18432,
            "summary": "While the Transformer architecture has become the de-facto standard for natural language processing tasks, its applications to computer vision remain limited. In vision, attention is either applied in conjunction with convolutional networks, or used to replace certain components of convolutional networks while keeping their overall structure in place..."
        }
    ]
    
    print("# Most Cited Papers from Recent arXiv Submissions")
    print("*Analysis of papers submitted in the last 1 day(s)*")
    print()
    
    for paper in results:
        print(f"\n## {paper['rank']}. [{paper['title']}](https://arxiv.org/abs/{paper['arxiv_id']})")
        print(f"- **arXiv ID**: {paper['arxiv_id']}")
        print(f"- **Cited by recent papers**: {paper['cited_by_recent']} times")
        print(f"- **Total citations**: {paper['total_citations']:,}")
        print()
        summary = paper['summary']
        if len(summary) > 300:
            summary = summary[:300] + "..."
        print(summary)
    
    print()
    print("=" * 70)
    print("Key Insights:")
    print("=" * 70)
    print()
    print("✅ Foundation Models Dominate:")
    print("   - Transformer architecture papers (Attention, BERT, GPT-3) are")
    print("     consistently cited by today's research")
    print()
    print("✅ Cross-Domain Impact:")
    print("   - Papers span NLP, Computer Vision, and general ML")
    print("   - Shows interdisciplinary nature of modern AI research")
    print()
    print("✅ Reliable Signal:")
    print("   - Recent citations provide more reliable quality signal than")
    print("     paper titles or abstracts alone")
    print()
    print("=" * 70)


def show_integration_examples():
    """Show how to integrate with existing code"""
    
    print("\n\n")
    print("=" * 70)
    print("Integration Examples")
    print("=" * 70)
    print()
    
    print("1. Standalone CLI Usage:")
    print("-" * 70)
    print("""
# Basic usage
python arxiv_citations.py --categories cs.AI cs.LG --days 1 --top-n 10

# With different parameters
python arxiv_citations.py --categories cs.DC cs.AR --days 3 --top-n 15 --min-citations 3

# With API key for higher rate limits
python arxiv_citations.py --api-key YOUR_KEY --categories cs.AI
""")
    
    print("\n2. Integration with Research Module:")
    print("-" * 70)
    print("""
from research import Research

# Enable citation ranker
research = Research(use_citation_ranker=True)

# Run citation analysis
result = research.pull_data_with_citations(
    days=1,
    top_n=10,
    min_citations=2
)

print(result)
""")
    
    print("\n3. Programmatic Usage:")
    print("-" * 70)
    print("""
from arxiv_citations import ArxivCitationAnalyzer

# Initialize analyzer
analyzer = ArxivCitationAnalyzer()

# Run analysis
results = analyzer.analyze(
    categories=['cs.AI', 'cs.LG'],
    days=1,
    max_papers=50,
    top_n=10,
    min_citations=2
)

# Format and display
output = analyzer.format_results(results)
print(output)
""")


def show_use_cases():
    """Show example use cases"""
    
    print("\n\n")
    print("=" * 70)
    print("Use Cases")
    print("=" * 70)
    print()
    
    use_cases = [
        {
            "title": "📚 Literature Review",
            "description": "Identify key papers to read when starting research in a new area"
        },
        {
            "title": "🔍 Research Tracking",
            "description": "Monitor which foundational papers are gaining traction in recent work"
        },
        {
            "title": "📊 Research Trends",
            "description": "Understand what techniques/methods today's researchers are building on"
        },
        {
            "title": "🎯 Quality Filter",
            "description": "Use citation counts as a more reliable signal than just paper titles"
        },
        {
            "title": "🔗 Connection Discovery",
            "description": "Find unexpected connections between different research areas"
        }
    ]
    
    for uc in use_cases:
        print(f"\n{uc['title']}")
        print(f"   {uc['description']}")
    
    print()


if __name__ == "__main__":
    print_demo_output()
    show_integration_examples()
    show_use_cases()
    
    print()
    print("=" * 70)
    print("Note: This is demo output. In a real environment with network access,")
    print("the tool would fetch actual data from arXiv and Semantic Scholar APIs.")
    print("=" * 70)
    print()
