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


class Emailer:
    def __init__(self):
        self.from_email = os.environ.get('FROM_EMAIL')
        self.to_email = os.environ.get('TO_EMAIL')
        self.password = os.environ.get('GOOGLE_APP_PW')

        if not all([self.from_email, self.to_email, self.password]):
            raise ValueError("Missing required environment variables: FROM_EMAIL, TO_EMAIL, GOOGLE_APP_PW")

    def send_email(self, content: str, subject: str = None, to_addr: str = None) -> None:
        """Send an email with markdown content."""
        if to_addr is None:
            to_addr = self.to_email

        if subject is None:
            subject = f"H3LPeR {datetime.now().strftime('%Y-%m-%d')}"

        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(markdown(content), subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.from_email, self.password)
            server.send_message(msg)

    def _connect_imap(self):
        """Connect to Gmail IMAP server."""
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
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
