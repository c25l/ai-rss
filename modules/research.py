import numpy as np
import subprocess
import psycopg2
from claude import Claude as Generator
import feedbiz
import requests
from predict_acceptance import ResearchPredictor

class Research:
    articles = []
    article_prompt = """1. You will be given a paper represented as title, link and abstract. This paper is from a large list of new preprints.
    2. Your job is to analyze the paper and determine if it is worth consideration according to the following directions and preferences, if it is, we "ACCEPT" it, otherwise we "REJECT" it.

### Quality Filtering (Apply Rigorous Standards):
**REJECT papers with these red flags:**
- Big claims without big evidence
- Vague mathematical formalism
- Missing baselines/comparisons
- Buzzword bingo (mixing unrelated trending fields)
- Prominent AI tool acknowledgments

**Accept only papers that:**
- Make testable, precisely stated claims
- Have logical mathematical connections
- Use proper experimental methodology
- Prioritize substance over jargon

**Research Preferences:**
- machine learning and computational linguistics
- large language models
- embeddings
- transformers
- statistical methodology. 

**Particular interest in**:
- the theoretical foundations of AI systems
- representation learning
- computer science with statistical applications.

**Not interested in**:
- AGI
- driving
- protein
- privacy

Please reply with only "ACCEPT" or "REJECT" and nothing else, do not include any other text, just the word "ACCEPT" or "REJECT".
"""
    output_prompt= """
Progressive analysis of AI/ML papers from the last day.

### Paper Collection Strategy:
1. You will be given a huge list of papers in the research section. Iterate through these keeping the best 5.
3. **Build progressively**: Update your recommendations as you discover better papers in later batches

### Quality Filtering (Apply Rigorous Standards):
**REJECT papers with these red flags:**
- Big claims without big evidence
- Vague mathematical formalism
- Missing baselines/comparisons
- Buzzword bingo (mixing unrelated trending fields)
- Prominent AI tool acknowledgments

**Accept only papers that:**
- Make testable, precisely stated claims
- Have logical mathematical connections
- Use proper experimental methodology
- Prioritize substance over jargon

**Research Preferences:**
- machine learning and computational linguistics
- large language models
- embeddings
- transformers
- statistical methodology. 

**Particular interest in**:
- the theoretical foundations of AI systems
- representation learning
- computer science with statistical applications.

**Not interested in**:
- AGI
- driving
- protein
- privacy

### Output Requirements:
return a markdown formatted string with the following sections:
```markdown
## ArXiv Research Digest

### Top Papers (Analyzed [X] of [Y] total papers)
[Best 3-5 papers with abstracts and analysis]

### Notable Mentions
[Additional interesting papers worth tracking]

### Research Trends
[Patterns observed across all papers]
Please return the document in markdown as output.
"""
    def __init__(self):
        self.articles = []

    def section_title(self):
        return "Arxiv Review"
    
    def db_upload(self, xx, accepted):
        try:
            dsn ="dbname=airss host=localhost"

            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS research_reviews (
                    id SERIAL PRIMARY KEY,
                    article_text TEXT,
                    accepted BOOLEAN,
                    model_response TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
            """)

            cur.execute(
                "INSERT INTO research_reviews (article_text, accepted) VALUES (%s, %s)",
                (xx, accepted)
            )

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print("no db?",e)

    def claude_predict(self, research_prompt, xx):
        output=Generator().generate(research_prompt + "\n\n" + xx.replace('"', '\\"').replace("'", "\\'"))
        #output = ollama("\no_think\n"+research_prompt + "\n\n" + xx.replace('"', '\\"').replace("'", "\\'"), model="qwen3:8b")

        accepted = True if "ACCEPT" in (output or "").upper() else False
        if accepted:
            return xx
        return None
        #    Try Postgres first, fall back to SQLite. Rely on DB defaults for created_at.

    def get_nomic_embedding(self, text):
        try:
            response = requests.post("http://localhost:11434/api/embeddings",
                                   json={"model": "nomic-embed-text", "prompt": text[:8000]},
                                   timeout=10)
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                if embedding and len(embedding) == 768:
                    return np.array(embedding)
            return None
        except Exception as e:
            return None
 
    def model_predict(self, abstract):
        coeffs =   {569: 0.3020383950085799, 369: 0.2723374048183833, 344: 0.2661472163465615, 256: 0.2648458651954586, 546: 0.2637415586101207, 491: -0.2618081851330004, 618:  -0.2596646121385572, 76: 0.24262965132536773, 272: 0.23763346991782386, 506: 0.23220220045437642, 20: -0.2304201014922505, 243: 0.22640853946667797, 14:  -0.22372119685357306, 325: -0.22352514453852068, 717: 0.2230093433167437, 592: 0.22238085499970753, 222: -0.21956167204475074, 529: -0.21946962432475914, 627:  0.21795278701217854, 371: -0.21464890471406944, 58: 0.2138007886557637, 113: -0.21029765260088015, 557: -0.20386227325440728, 623: 0.20182722303354586, 735:  0.2014196621480735, 394: -0.19949893891878465, 545: 0.19845247180634365, 526: 0.1981219338736734, 331: -0.1968212161188199, 48: 0.19617066488638482, 399:  -0.19591594556152633, 267: 0.19263210650408202, 439: 0.19075556831186818, 157: 0.19025468186689914, 455: -0.18688954019683213, 624: -0.18526596056834452, 437:  -0.1826605883628, 57: -0.18031821945358265, 456: -0.17894255731383915, 402: -0.17618304642156646, 763: 0.17593920791650883, 393: 0.17572613083109112, 171:  -0.17542363809281972, 585: 0.17531170393110854, 478: 0.17441720051367912, 543: 0.17337217415353062, 442: -0.17223429711365168, 573: 0.17051035778740373, 539:  -0.17002688878065164, 425: 0.16625741292889215}
        pred = self.get_nomic_embedding(abstract)
        if pred is not None:
            raw=sum([yy*pred[xx] for xx,yy in coeffs.items()])
            return raw
        else:
            return 0.0
    def pull_data(self):
        self.articles = feedbiz.feedbiz("research", whitelist=["Announce Type: new"])
        if self.articles == []:
            return
        outputs = []
        print("going to predict")
        probs = [[xx,self.model_predict(xx)] for xx in self.articles]
        print("predicted")
        for xx,yy in probs:
            self.db_upload(xx, (yy>0).astype(bool))
        probs.sort(key=lambda x: x[1], reverse=True)
        outputs = [xx[0] for xx in probs[:10]]
        print("Research:", len(outputs), " / ", len(self.articles))
        self.articles = outputs

    def output(self):
        print("made it here?")
        if not self.articles:
            return "No research articles found."
        try:
            temp = Generator().generate(self.output_prompt + "\n\n" + "\n".join([xx.replace('"', '\\"').replace("'", "\\'") for xx in self.articles]))
            if not temp:
                raise Exception("No output from Claude")
            return temp
        except Exception as e:
            print("Error generating research output:", e)
            return "\n".join(self.articles)

if __name__ == "__main__":
    print("loading object")
    xx = Research()
    print("pulling data")
    xx.pull_data()
    print("rendering output")
    print(xx.output())

