import json
import numpy as np
import os
import requests
from datamodel import Article
import azureopenai

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_TINY_MODEL = "llama3.2:1b-instruct-q6_K"
DEFAULT_SUMMARY_MODEL="phi3.5:3.8b-mini-instruct-q6_K"
DEFAULT_OPTIONS = {
    "temperature": 0.0,
    "top_p": 0.9,
    "stop": None,  # You can add stop sequences later if needed
}
class Generator(object):
    def get_article_keywords(self, article):
        summary = " ".join(article.summary.split(" ")[:100]).replace("\"", "\\\"")

        kwd_prompt = f"""You are a research assistant.         
    The following article is part of a news corpus structured into the following sections, which are available as classifications:

    The article is as follows:
    ```json
    {{
    "source":"{article.source}",
    "title": "{article.title}",
    "summary": "{summary}",
    "source_keywords": "{', '.join(article.keywords)}",
    }}
    ```

    You will return a json object. 
    Under the key "Keywords", give 3-6 keywords describing the content. Prefer fewer keywords to wrong or weak ones. 
        If there are any named entities or organizations, include them in the keywords. 
    Under the key "Claims", provide a list of claims made by the article. Each of these claims should be a single sentence.
    Under the key "Section", provide the section of the news corpus that this article belongs to. Select from the following sections:
    ["World","Politics","Business","Technology","Science","Education","Health","Arts ,"Opinion","Environment"]
    If you feel the need to include reasoning, you can add a key "Reasoning" with a short explanation of your choices.
    Return only the keywords as a list (3-6 max) (as a list), and a short reason in this format:
    ```json
    {{
        "Keywords": [key1, key2, ...], 
        "Claims":[claim1, claim2, ...],
        "Section": "Section Name",
        "Reasoning": "Optional" 
    }}
    ```
        Do not add any other text. The output must be a valid json object.
        """
        response = self.generate(kwd_prompt, model_name=DEFAULT_SUMMARY_MODEL)
        print(response)
        resp = self.interpret(response, {})

        # Convert keywords and claims into ORM objects
        article.keywords = resp.get('Keywords', resp.get('keywords', []))
        cl=resp.get('Claims', resp.get('claims',[article.title]))
        sect = resp.get('Section', resp.get('section', 'Other'))
        article.claims = [article.title+ "\n"+ article.summary[0:500]]
        emb = self.embed("\n".join(cl))
        article.section = sect
        article.vector = emb
        return article
    
    
    def interpret(self, raw_result, default=[]):
        # Interpret the raw result from the model
        # This is a placeholder; actual implementation will depend on the model's output format

        if raw_result.startswith("```json"):
            raw_result = "\n".join(raw_result.split("\n")[1:-1])
        if raw_result.endswith(",}"):
            raw_result = raw_result[:-2]+"}"
        if raw_result.endswith(",]"):
            raw_result = raw_result[:-2]+"]"
        if "}\n\n{" in raw_result:
            raw_result = raw_result.split("}\n\n{")[0]+"}"
        try:
            return json.loads(raw_result)
        except json.JSONDecodeError:
            print(f"[ERROR] Failed to decode JSON: {raw_result}")
            return default

    def summary_arts(self, arts):
        print(arts)
        arts2="\n".join(["- "+ cc.title + " -- " + cc.summary[0:200] for cc in arts[0:4]])
        prompt=f"""
You will be presented with a list of article titles which embody a current event. in 10 words or fewer you will tell what the articles have in common.
Return only this. do not explain what you are doing. Anything beyond 10 words is unacceptable.

Here are the titles:
    {arts2}
return your answer as a json object with a single key "summary" and the value as above.
        """

        response = self.generate(prompt, model_name=DEFAULT_TINY_MODEL)
        print(response)
        response = self.interpret(response, {})
        return response.get("summary",response.get("Summary","oopsy"))
    
    def generate(self, prompt, model_name=DEFAULT_MODEL, options = None):
        """
        Send a prompt to the specified model via Ollama and return the response text.
        """
        print("Model:", model_name)
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
            return data.get("response", "").split("</think>")[-1].strip()
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

