# H3lPeR - Personal Briefing System

Take whatever out of here. It's mostly llm stuff, but the ideas that made the vector embeddings clustering for news and the recursive ranker for articles were actual ideas and do help a lot.

## LLMs for ranking

You can have llms rank things. In test cases that ranking will be quite good, but thrown headlong into production, not so much. 
It's much more visible in small language models in the 3-14B range (early 2026) as they can often work up into teens of articles successfully but never into the 20s. 
If we pull the ranking implementation back into code, the llm can operate much smaller batches that are intrinsically much easier.

To get the top 5 or so, out of batches of maybe 20 (you can do 15 for small models and all still works pretty well). What if you need more than the window size? Get the top N, then remove them from the set and rank again. Many of the intermediate steps and old rankings can be reused for this purpose.  

## LLMs for news
Ranking the news wasn't as rewarding. It's better grouped and organized.
I find that you can embed the news articles and group them pretty easily (using standard vector grouping stuff in numpy. Dealer's choice on the details, there's no clear winner but all are different).

I find that today's (early 2026) llms do much better if you're not having them write anything. Using them to rank is good, but it's better to reuse the article text than have them summarize.
