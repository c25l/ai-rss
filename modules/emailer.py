from datetime import datetime
from markdown import markdown
import smtplib
from email.message import EmailMessage
import os
 
def send_email(result: str, subject: str = None) -> None:
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.mail.me.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))

    if not sender:
        raise ValueError("EMAIL_SENDER environment variable is required")
    if not receiver:
        raise ValueError("EMAIL_RECEIVER environment variable is required")
    if not password:
        raise ValueError("EMAIL_PASSWORD environment variable is required")

    if subject is None:
        subject = f"Morning News for {datetime.now().strftime('%Y-%m-%d')}"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(markdown(result), subtype="html")
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(msg['From'], password)
        server.send_message(msg)