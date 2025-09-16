import os
import fcntl
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime

# Configuration
BUFFER_FILE = "/Users/chris/source/airss/outbox_buffer.json"

def load_buffer():
    """Load the current buffer state from file"""
    if not os.path.exists(BUFFER_FILE):
        return {
            "accumulated_content": "",
            "subject": f"📰 {datetime.now().strftime('%Y-%m-%d')}",
            "last_updated": datetime.now().isoformat()
        }
    
    try:
        with open(BUFFER_FILE, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "accumulated_content": "",
            "subject": f"📰 {datetime.now().strftime('%Y-%m-%d')}",
            "last_updated": datetime.now().isoformat()
        }

def save_buffer(buffer_data):
    """Save buffer state to file with file locking"""
    with open(BUFFER_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump(buffer_data, f, indent=2)
        f.flush()


def format_group_for_narrative(group_text, articles_data):
    """Format a single group for narrative generation"""
    articles_text = ""
    for article in articles_data:
        articles_text += f"- **{article['title']}** ({article['source']})\n"
        articles_text += f"  Summary: {article['summary']}\n"
        articles_text += f"  URL: {article['url']}\n\n"
    
    return f"## {group_text}\n\n{articles_text}"

def send_email(markdown_content: str, subject: str) -> dict:
    """Helper function to send email"""
    try:
        # Convert markdown to HTML properly
        from markdown import markdown
        html_body = markdown(markdown_content, extensions=['extra', 'codehilite'])
        
        # Add proper HTML styling
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        strong {{ color: #2c3e50; }}
        em {{ color: #7f8c8d; }}
        hr {{ border: none; border-top: 2px solid #ecf0f1; margin: 30px 0; }}
        ul {{ margin: 15px 0; }}
        li {{ margin: 8px 0; }}
        blockquote {{ 
            border-left: 4px solid #3498db; 
            margin: 20px 0; 
            padding-left: 20px; 
            color: #7f8c8d; 
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
        
        
        sender = "christopherpbonnell@icloud.com"
        receiver = "christopherpbonnell+airss@gmail.com"
        password = "vqxh-oqrp-wjln-eagl"  # Should be environment variable
        
        # Create and send email
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(html_content, subtype="html")
        
        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(msg['From'], password)
            server.send_message(msg)
        
        return {"success": True, "message": "Email sent successfully."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def add(content, subject=""):
    """Handle add tool - add content to buffer"""
    if subject == "":
        subject = f"📰 {datetime.now().strftime('%Y-%m-%d')}"
    
    try:
        buffer_data = load_buffer()
        
        # If buffer is empty, set the subject
        if not buffer_data["accumulated_content"].strip():
            buffer_data["subject"] = subject
        
        # Add separator if buffer has content
        if buffer_data["accumulated_content"].strip():
            buffer_data["accumulated_content"] += "\n\n"
        
        # Append new content
        buffer_data["accumulated_content"] += content
        buffer_data["last_updated"] = datetime.now().isoformat()
        
        save_buffer(buffer_data)
        
        return {"success": True, "message": "Content added to buffer."}        
    except Exception as e:
        return {"success": False, "message": str(e)}

def clear():
    """Handle clear tool - clear buffer without sending"""
    try:
        buffer_data = load_buffer()
        buffer_data["accumulated_content"] = ""
        buffer_data["last_updated"] = datetime.now().isoformat()
        save_buffer(buffer_data)
        
        return True        
    except Exception as e:
        return e

def send_all():
    """Handle send_all tool - send buffer and clear"""
    try:
        buffer_data = load_buffer()
        
        if not buffer_data["accumulated_content"].strip():
            return False        
        # Send the accumulated content
        result = send_email(buffer_data["accumulated_content"], buffer_data["subject"])
        
        # Clear the buffer
        clear()
        buffer_data["accumulated_content"] = ""
        buffer_data["last_updated"] = datetime.now().isoformat()
        save_buffer(buffer_data)
        
        result["message"] = f"Accumulated content sent and buffer cleared. {result['message']}"
        return True
        
    except Exception as e:
        return e
