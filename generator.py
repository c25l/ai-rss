import json
import numpy as np
import os
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential

class Generator(object):
	def __init__(self, endpt,api_key):
		self.client = AzureOpenAI(azure_endpoint=endpt,api_key=api_key,api_version="2024-05-01-preview")
		self.news_blocks = """- **World** — international news, global events,
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

	Source: {article.source}
	Title: {article.title}
	Summary: {" ".join(article.summary.split(" ")[:100])}

	The upstream summary typically has these topics: {",".join(article.keywords)}

	You will give 3-6  keywords describing the content. Prefer fewer keywords to wrong or weak ones, 
	and provide a reason that demonstrates that they are supported by the text.

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
	def generate(self, text, prompt=None, model='4.1-nano'):
		model_name = "gpt-4.1-nano"
		if model == '4.1-mini':
			model_name = "gpt-4.1-mini"

		messages=[]
		if prompt!=None:
			messages.append({"role":"system","content":prompt})
		messages.append({"role":"user","content":text})
			
		response = self.client.chat.completions.create(
		   messages=messages,
			max_tokens=800,
			temperature=0.0,
			top_p=1.0,
			frequency_penalty=0.0,
			presence_penalty=0.0,
			model=model_name
		)

		return response.choices[0].message.content
	def embed(self, text, norm=True):
		model_name = "text-embedding-3-small"

		if type(text)==str:
			text = [text]
		response = self.client.embeddings.create(
			input=text,
			model=model_name
		)
		embeddings = [np.array(item.embedding) for item in response.data]
		if norm:
			embeddings = [emb/np.linalg.norm(emb) for emb in embeddings]

		return embeddings; 

