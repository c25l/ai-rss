from datetime import datetime
from markdown import markdown
import smtplib
from email.message import EmailMessage
 
def send_email(result: str, subject: str = None) -> None:
    sender = "christopherpbonnell@icloud.com"
    receiver = "christopherpbonnell@gmail.com"
    password="vqxh-oqrp-wjln-eagl"

    if subject is None:
        subject = f"Morning News for {datetime.now().strftime('%Y-%m-%d')}"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(markdown(result), subtype="html")
    with smtplib.SMTP("smtp.mail.me.com", 587) as server:
        server.starttls()
        server.login(msg['From'], password)
        server.send_message(msg)