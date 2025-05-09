import smtplib
from email.message import EmailMessage
from markdown import markdown
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from collections import defaultdict
import json
from database import Database

class Outputs:
	@staticmethod
	def send_email(text,sender, receiver, password):
		msg = EmailMessage()
		msg["From"] = sender
		msg["To"] = receiver
		msg["Subject"] = f"{datetime.now().strftime('%Y-%m-%d')}"
		msg.set_content(markdown(text), subtype="html")
		with smtplib.SMTP("smtp.mail.me.com", 587) as server:
			server.starttls()
			server.login(msg['From'], password)
			server.send_message(msg)

	@staticmethod
	def md_fileout(text,dest):
		prelude="""# Tasks
```dataview
TASK 
WHERE !completed
GROUP BY file.name
```
"""
		filename = f"{dest}/Briefing-{datetime.now().strftime('%Y-%m-%d')}.md"
		with open(filename, "w") as f:
			f.write(prelude+text)
			

# Azure Blob Storage configuration
class AzureOut:
	def __init__(self,db):
		self.AZURE_STORAGE_CONNECTION_STRING =db.get_secret('airsscontainer-container-connection-string')
		self.AZURE_CONTAINER_NAME = db.get_secret('airsscontainer-container-name')
	
	def upload_to_azure(self, blob_name, data, content_type="application/json"):
		"""
		Upload data to Azure Blob Storage.

		Parameters:
		- blob_name: Name of the blob in Azure Storage.
		- data: Data to upload (bytes or string).
		- content_type: MIME type of the data.
		"""
		try:
			blob_service_client = BlobServiceClient.from_connection_string(self.AZURE_STORAGE_CONNECTION_STRING)
			blob_client = blob_service_client.get_blob_client(container=self.AZURE_CONTAINER_NAME, blob=blob_name)

			if isinstance(data, str):
				data = data.encode("utf-8")  # Convert string to bytes
			settings = ContentSettings(content_type=content_type)
			blob_client.upload_blob(data, overwrite=True, content_settings=settings)
			print(	f"Uploaded {blob_name} to Azure Blob Storage.")
		except Exception as e:
			print(	f"Failed to upload {blob_name} to Azure: {e}")

	def write_d3_bundle_to_azure(self,
		date_str,
		articles
	):
		"""
		Generate D3 graph bundle in memory and upload to Azure Blob Storage.

		Parameters:
		- date_str: e.g. '2025-04-03'
		- articles: list of {
			"title", "url", "source", "date", "score",
			"keywords": [str], "clusters": [str]
		}
		"""
		# Convert datetime objects in articles to strings
		for article in articles:
			if isinstance(article["published"], datetime):
				article["published"] = article["published"].strftime('%Y-%m-%d')

		# Generate nodes and links
		nodes = [{'id': yy, 'size': 10} for yy in set([xx for aa in articles for xx in aa['keywords']])]
		links = []
		temp = defaultdict(int)
		for aa in articles:
			for ii, bb in enumerate(aa['keywords']):
				for jj in aa['keywords'][ii + 1:]:
					temp[f"{bb}||{jj}"] += 1
		for ii, xx in temp.items():
			bb, jj = ii.split("||")
			links.append({"source": bb, "target": jj, "value": xx})

		# Prepare data as JSON strings
		graph_json = json.dumps({"nodes": nodes, "links": links}, indent=2)
		articles_json = json.dumps(articles, indent=2)
		latest_json = json.dumps({
			"date": date_str,
			"graph": f"{date_str}/graph.json",
			"articles": f"{date_str}/articles.json"
		}, indent=2)

		# Upload to Azure Blob Storage
		self.upload_to_azure(f"{date_str}/graph.json", graph_json)
		self.upload_to_azure(f"{date_str}/articles.json", articles_json)
		self.upload_to_azure("latest.json", latest_json)

		# Update manifest.json
		manifest_blob_name = "manifest.json"
		try:
			blob_service_client = BlobServiceClient.from_connection_string(self.AZURE_STORAGE_CONNECTION_STRING)
			blob_client = blob_service_client.get_blob_client(container=self.AZURE_CONTAINER_NAME, blob=manifest_blob_name)

			if blob_client.exists():
				manifest = json.loads(blob_client.download_blob().readall().decode("utf-8"))
			else:
				manifest = []

			if date_str not in manifest:
				manifest.append(date_str)
				manifest.sort(reverse=True)

			manifest_json = json.dumps(manifest, indent=2)
			self.upload_to_azure(manifest_blob_name, manifest_json)
		except Exception as e:
			print(	f"Failed to update manifest.json: {e}")

		print(	f"✅ Uploaded {len(nodes)} nodes, {len(links)} links, {len(articles)} articles to Azure Blob Storage.")
