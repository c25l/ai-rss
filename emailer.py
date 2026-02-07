from datetime import datetime
from markdown import markdown
import smtplib
import imaplib
import email
from email.message import EmailMessage
from email.header import decode_header
import os
import re
from bs4 import BeautifulSoup


# Simple color scheme - no longer needed, kept for backward compatibility
# Colors are now hardcoded in the simple HTML template


class Emailer:
    def __init__(self):
        self.from_email = os.environ.get('FROM_EMAIL')
        self.to_email = os.environ.get('TO_EMAIL')
        self.password = os.environ.get('GOOGLE_APP_PW')

        if not all([self.from_email, self.to_email, self.password]):
            raise ValueError("Missing required environment variables: FROM_EMAIL, TO_EMAIL, GOOGLE_APP_PW")

    def _create_simple_html(self, content: str, subject: str) -> str:
        """Convert markdown content to clean, minimally-styled HTML."""
        # Convert markdown to HTML first
        html_content = markdown(content)

        # Parse HTML to add simple, clean styling
        soup = BeautifulSoup(html_content, 'html.parser')

        # Style h1 headers - simple and clean
        for h1 in soup.find_all('h1'):
            h1['style'] = (
                "color: #2c3e50;"
                "font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                "font-size: 24px;"
                "font-weight: 600;"
                "margin: 24px 0 12px 0;"
                "padding-bottom: 8px;"
                "border-bottom: 2px solid #3498db;"
            )

        # Style h2 headers
        for h2 in soup.find_all('h2'):
            h2['style'] = (
                "color: #34495e;"
                "font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                "font-size: 20px;"
                "font-weight: 600;"
                "margin: 20px 0 10px 0;"
            )

        # Style h3 headers
        for h3 in soup.find_all('h3'):
            h3['style'] = (
                "color: #546e7a;"
                "font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                "font-size: 16px;"
                "font-weight: 600;"
                "margin: 16px 0 8px 0;"
            )

        # Style links
        for link in soup.find_all('a'):
            link['style'] = (
                "color: #3498db;"
                "text-decoration: none;"
            )

        # Style paragraphs
        for p in soup.find_all('p'):
            p['style'] = (
                "color: #2c3e50;"
                "font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                "font-size: 14px;"
                "line-height: 1.6;"
                "margin: 8px 0;"
            )

        # Style lists
        for ul in soup.find_all('ul'):
            ul['style'] = (
                "color: #2c3e50;"
                "font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;"
                "font-size: 14px;"
                "line-height: 1.7;"
                "margin: 8px 0;"
            )
        
        # Add <br> tags after list items for better spacing
        for li in soup.find_all('li'):
            # Append a <br> tag at the end of each list item
            li.append(soup.new_tag('br'))

        # Style strong/bold text
        for strong in soup.find_all('strong'):
            strong['style'] = (
                "color: #2c3e50;"
                "font-weight: 600;"
            )

        # Style horizontal rules
        for hr in soup.find_all('hr'):
            hr['style'] = (
                "border: none;"
                "border-top: 1px solid #dfe6e9;"
                "margin: 24px 0;"
            )

        styled_content = str(soup)

        # Create simple, clean email template
        simple_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="
            background-color: #f5f6fa;
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        ">
            <div style="
                max-width: 700px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <!-- Header -->
                <div style="
                    background-color: #3498db;
                    color: #ffffff;
                    padding: 20px 24px;
                    font-size: 22px;
                    font-weight: 600;
                ">
                    {subject}
                </div>

                <!-- Content -->
                <div style="
                    padding: 24px;
                    color: #2c3e50;
                ">
                    {styled_content}
                </div>

                <!-- Footer -->
                <div style="
                    background-color: #ecf0f1;
                    padding: 12px 24px;
                    font-size: 11px;
                    color: #7f8c8d;
                    text-align: right;
                ">
                    {datetime.now().strftime('%Y-%m-%d')}
                </div>
            </div>
        </body>
        </html>
        """

        return simple_html

    def send_email(self, content: str, subject: str = None, to_addr: str = None) -> None:
        """Send an email with markdown content in simple, clean styling."""
        if to_addr is None:
            to_addr = self.to_email

        if subject is None:
            subject = f"H3LPeR {datetime.now().strftime('%Y-%m-%d')}"

        # Create simple, clean HTML
        styled_html = self._create_simple_html(content, subject)

        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(styled_html, subtype="html")

        with smtplib.SMTP("smtp.mail.me.com", 587) as server:
            server.starttls()
            server.login(self.from_email, self.password)
            server.send_message(msg)

    def _connect_imap(self):
        """Connect to iCloud IMAP server."""
        mail = imaplib.IMAP4_SSL("imap.mail.me.com")
        mail.login(self.from_email, self.password)
        return mail

    def _decode_header(self, header):
        """Decode email header."""
        if header is None:
            return ""
        decoded = decode_header(header)
        result = []
        for content, encoding in decoded:
            if isinstance(content, bytes):
                result.append(content.decode(encoding or 'utf-8', errors='ignore'))
            else:
                result.append(content)
        return ''.join(result)

    def _extract_body(self, msg):
        """Extract clean text from email body."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        body = soup.get_text(separator=' ', strip=True)
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())

        return body.strip()

    def _parse_email(self, raw_email, email_id=None):
        """Parse raw email into clean dict."""
        msg = email.message_from_bytes(raw_email)

        subject = self._decode_header(msg.get("Subject", ""))
        from_ = self._decode_header(msg.get("From", ""))
        to_ = self._decode_header(msg.get("To", ""))
        date = msg.get("Date", "")
        body = self._extract_body(msg)

        # Create snippet (first 150 chars)
        snippet = body[:150] + "..." if len(body) > 150 else body

        return {
            "subject": subject,
            "from": from_,
            "to": to_,
            "date": date,
            "snippet": snippet,
            "_full_body": body,
            "_msg": msg,
            "_email_id": email_id
        }

    def read_inbox(self, limit: int = 20, folder: str = "INBOX"):
        """Read recent emails from specified folder."""
        mail = self._connect_imap()
        mail.select(f'"{folder}"' if "/" in folder else folder)

        _, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()

        # Get most recent emails
        recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        recent_ids = reversed(recent_ids)  # Most recent first

        emails = []
        for email_id in recent_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            emails.append(self._parse_email(raw_email))

        mail.close()
        mail.logout()

        return emails

    def read_starred(self, limit: int = 20):
        """Read starred/flagged emails."""
        mail = self._connect_imap()
        mail.select("INBOX")

        _, messages = mail.search(None, "FLAGGED")
        email_ids = messages[0].split()

        # Get most recent starred
        recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        recent_ids = reversed(recent_ids)

        emails = []
        for email_id in recent_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            emails.append(self._parse_email(raw_email))

        mail.close()
        mail.logout()

        return emails

    def search_emails(self, query: str, limit: int = 20):
        """Search emails by subject or from address."""
        mail = self._connect_imap()
        mail.select("INBOX")

        # Try searching in subject first, then from
        _, messages = mail.search(None, f'OR SUBJECT "{query}" FROM "{query}"')
        email_ids = messages[0].split()

        recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        recent_ids = reversed(recent_ids)

        emails = []
        for email_id in recent_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            emails.append(self._parse_email(raw_email))

        mail.close()
        mail.logout()

        return emails

    def get_email_body(self, email_dict: dict) -> str:
        """Get full body text from an email dict returned by other methods."""
        return email_dict.get("_full_body", "")

    def _is_date_subject(self, subject: str) -> bool:
        """Check if subject matches date patterns: YYYY-MM-DD, yyyymmdd, yymmdd, YY-MM-DD."""
        if not subject:
            return False

        # Remove whitespace and convert to string
        subject = subject.strip()

        # Pattern: YYYY-MM-DD (e.g., 2025-12-05)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', subject):
            return True

        # Pattern: YY-MM-DD (e.g., 25-12-05)
        if re.match(r'^\d{2}-\d{2}-\d{2}$', subject):
            return True

        # Pattern: yyyymmdd (e.g., 20251205)
        if re.match(r'^\d{8}$', subject):
            return True

        # Pattern: yymmdd (e.g., 251205)
        if re.match(r'^\d{6}$', subject):
            return True

        return False

    def read_drafts(self, limit: int = 20):
        """Read draft emails from Gmail Drafts folder."""
        mail = self._connect_imap()

        # Gmail stores drafts in [Gmail]/Drafts
        mail.select('"[Gmail]/Drafts"')

        _, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()

        # Get most recent drafts
        recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        recent_ids = reversed(recent_ids)  # Most recent first

        drafts = []
        for email_id in recent_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            drafts.append(self._parse_email(raw_email, email_id))

        mail.close()
        mail.logout()

        return drafts

    def delete_draft(self, email_id):
        """Delete a draft email by its ID."""
        mail = self._connect_imap()
        mail.select('"[Gmail]/Drafts"')

        # Mark for deletion and expunge
        mail.store(email_id, '+FLAGS', '\\Deleted')
        mail.expunge()

        mail.close()
        mail.logout()

    def send_matching_drafts(self) -> dict:
        """
        Find and send drafts that match criteria:
        - Subject is a date (YYYY-MM-DD, yyyymmdd, yymmdd, YY-MM-DD)
        - OR recipient is cpbnel.news@gmail.com

        All matching drafts are sent to cpbnel.news@gmail.com with today's date as subject.
        Drafts are deleted after sending.

        Returns:
            dict with 'sent' count and 'details' list
        """
        drafts = self.read_drafts()
        sent_count = 0
        details = []

        for draft in drafts:
            subject = draft.get("subject", "")
            to = draft.get("to", "")
            body = draft.get("_full_body", "")
            email_id = draft.get("_email_id")

            # Check if draft matches criteria
            is_date_subject = self._is_date_subject(subject)
            is_news_recipient = "cpbnel.news@gmail.com" in to

            if is_date_subject or is_news_recipient:
                # Send with today's date as subject
                today_subject = datetime.now().strftime('%Y-%m-%d')

                try:
                    # Send the email
                    self.send_email(
                        content=body,
                        subject=today_subject,
                        to_addr="cpbnel.news@gmail.com"
                    )

                    # Delete the draft
                    if email_id:
                        self.delete_draft(email_id)

                    sent_count += 1
                    details.append({
                        "original_subject": subject,
                        "original_to": to,
                        "sent_subject": today_subject,
                        "sent_to": "cpbnel.news@gmail.com",
                        "matched_by": "date_subject" if is_date_subject else "news_recipient"
                    })
                except Exception as e:
                    details.append({
                        "original_subject": subject,
                        "error": str(e)
                    })

        return {
            "sent": sent_count,
            "details": details
        }


# Legacy function for backward compatibility
def send_email(result: str, subject: str = None) -> None:
    """Legacy send function - uses new Emailer class."""
    emailer = Emailer()
    emailer.send_email(result, subject)


if __name__ == "__main__":
    # Test usage
    emailer = Emailer()

    print("Testing inbox read...")
    inbox = emailer.read_inbox(limit=5)
    for i, email in enumerate(inbox):
        print(f"\n{i+1}. {email['subject']}")
        print(f"   From: {email['from']}")
        print(f"   Date: {email['date']}")
        print(f"   Snippet: {email['snippet'][:80]}")
