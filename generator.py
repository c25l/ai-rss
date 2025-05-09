import json
import numpy as np
import os
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma3:12b-it-qat"
DEFAULT_SMALL_MODEL = "qwen3:8b"
DEFAULT_TINY_MODEL = "llama3.2:1b-instruct-q6_K"
DEFAULT_OPTIONS = {
    "temperature": 0.0,
    "top_p": 0.9,
    "stop": None,  # You can add stop sequences later if needed
}
class Generator(object):
	news_blocks = """- **World** — international news, global events,
	- **Politics** —  legislation, governance
	- **Business** — companies, labor, economic policy  
	- **Technology** — software, hardware, AI
	- **Science** — discoveries, research
	- **Education** — schools, research, pedagogy
	- **Health** — medicine, disease, healthcare systems  
	- **Arts & Culture** — literature, film, music, philosophy  
	- **Opinion** — editorials, analysis  
	- **Environment** — climate change, conservation"""
	def get_article_keywords(self,article):
		summary = " ".join(article.summary.split(" ")[:100]).replace("\"","\\\"")

		kwd_prompt = f"""You will be classifying a news article for an expert reader.:
	This article is part of a news corpus structured into the following sections, which are available as classifications also:
	{self.news_blocks}

	To further help you anchor: 
	- Trump is currently the US president, he has extremely authoritarian tendencies. 
	He has started a trade war using tarrifs against everyone but especially china. 
	Elon Musk currently works for Trump as DOGE (Department of Government Efficiency), 
	which is destroying most of our more liberal institutions, and privatizing others with Palantir.
	
	- AI Models are evolving rapidly, and china has taken a leadership role in the domain. 
	The major players in the field are Google, Microsoft, Meta, OpenAI, Mistral, Anthropic, DeepSeek, AliBaba, and others.

	{{
	"source":"{article.source}",
	"title": "{article.title}",
	"summary": "{summary}",
	"source_keywords": "{", ".join(article.source_keywords)}",
	}}

	You will give 3-6  keywords describing the content. Prefer fewer keywords to wrong or weak ones, 
	and provide a reason that demonstrates that they are supported by the text.

	If the summary or source mentions and particular named entity or organization,
	you should include it in the keywords.

	Return only the keywords as a list (3-6 max) (as a list), and a short reason in this format:
	{{"Keywords": Keywords, "Reason":"Reason"}}
		Do not add any other text. The output must be a valid json object.
		"""
		response = self.generate(kwd_prompt)
		print(response)
		try:
			if response.startswith("```json"):
				response ="\n".join(response.split("\n")[1:-1])
			obj = json.loads(response)
			if type(obj["Keywords"])==str:
				obj["Keywords"] = [xx.strip() for xx in obj["Keywords"].split(",")]
			upstream = [xx.lower() for xx in article.keywords]
			downstream = [xx.lower() for xx in obj['Keywords']]
			kwds = [xx.title() for xx in upstream] + [xx.title() for xx in downstream if not any([yy for yy in upstream if xx in yy])]
			article.keywords = kwds
			return article
		except:
			print(	"failed to parse json",response)
		return article
	def summary_arts(self, arts):
		arts2="\n".join([bb.limited() for bb in arts])
		prompt=f"""
You will be presented with a list of articles which embody a central theme. From this, create a summary of the content in 10 words or fewer. 
If these articles are conceptually unrelated, it's okay to say so.
Return only this summary. do not explain what you are doing. Anything beyond 10 words is unacceptable.

Here are brief summaries of the articles involved:
	{arts2}
		"""

		response = self.generate(prompt)
		print(response)
		return response
	def generate(self, prompt, model_name=DEFAULT_MODEL	, options = None):
		"""
		Send a prompt to the specified model via Ollama and return the response text.
		"""
		payload = {
			"model": model_name,
			"prompt": prompt,
			"options": options if options else DEFAULT_OPTIONS,
			"stream": False,
		}
		try:
			response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
			response.raise_for_status()
			data = response.json()
			return data.get("response", "")
		except Exception as e:
			print(f"[ERROR] Model call failed: {e}")
			return "[ERROR]"

	def embed(self, text, pq = 'p',norm=True):
		payload = {
			"model": "nomic-embed-text",
			"prompt": ("passage: " if pq=='p' else "query: ") + text,
		}
		try:
			response = requests.post(f"{OLLAMA_BASE_URL}/api/embeddings", json=payload)
			response.raise_for_status()
			data = response.json()
			vect = np.array(data.get("embedding",[]))
			if norm:
				vect /= np.linalg.norm(vect)
			return vect
		except Exception as e:
			print(f"[ERROR] Model call failed: {e}")
			return []

