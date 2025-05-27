import smtplib
from email.message import EmailMessage
from markdown import markdown
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from collections import defaultdict
import json

class Outputs:
	@staticmethod
	def send_email(text,sender, receiver, password):
		msg = EmailMessage()
		msg["From"] = sender
		msg["To"] = receiver
		msg["Subject"] = f"Morning News for {datetime.now().strftime('%Y-%m-%d')}"
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
			
