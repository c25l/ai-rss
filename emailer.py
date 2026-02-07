from datetime import datetime
from markdown import markdown
import smtplib
import imaplib
import email
from email.message import EmailMessage
from email.header import decode_header
import html as html_mod
import json
import os
import re
from bs4 import BeautifulSoup


def validate_briefing_json(doc):
    """Validate a briefing JSON document against schema_version 1.

    Raises ValueError with a descriptive message on failure.
    """
    if not isinstance(doc, dict):
        raise ValueError("Briefing document must be a JSON object")
    for key in ("schema_version", "title", "date", "children"):
        if key not in doc:
            raise ValueError(f"Missing required top-level key: '{key}'")
    if doc["schema_version"] != 1:
        raise ValueError(f"Unsupported schema_version: {doc['schema_version']}")
    if not isinstance(doc["children"], list):
        raise ValueError("'children' must be a list")
    for i, child in enumerate(doc["children"]):
        _validate_node(child, path=f"children[{i}]")


def _validate_node(node, path=""):
    """Recursively validate a single node."""
    if not isinstance(node, dict):
        raise ValueError(f"Node at {path} must be an object")
    if "title" not in node or not isinstance(node["title"], str):
        raise ValueError(f"Node at {path} must have a string 'title'")
    if "children" in node:
        if not isinstance(node["children"], list):
            raise ValueError(f"'children' at {path} must be a list")
        for i, child in enumerate(node["children"]):
            _validate_node(child, path=f"{path}.children[{i}]")
    if "article" in node:
        art = node["article"]
        if not isinstance(art, dict):
            raise ValueError(f"'article' at {path} must be an object")


def render_briefing_content(doc):
    """Render briefing JSON sections to HTML fragments (no page wrapper).

    Returns the inner HTML suitable for embedding in any page chrome.
    """
    body_parts = []
    children = doc.get("children", [])
    for i, child in enumerate(children):
        body_parts.append(_render_section(child))
        if i < len(children) - 1:
            body_parts.append(
                '<hr style="border:none;border-top:1px solid #e0e4e8;margin:28px 0;">'
            )
    return "\n".join(body_parts)


def render_briefing_html(doc, subject=None):
    """Render a validated briefing JSON document to a complete HTML email string."""
    if subject is None:
        subject = doc.get("title", "H3LPeR Briefing")

    styled_content = render_briefing_content(doc)
    return _wrap_email_chrome(styled_content, subject)


# ---------- theme emoji lookup ----------

_SECTION_EMOJI = {
    "ai": "🤖", "artificial intelligence": "🤖", "machine learning": "🤖",
    "technology": "💻", "tech": "💻", "software": "💻", "developer": "💻",
    "science": "🔬", "research": "🔬", "nature": "🔬",
    "world": "🌍", "international": "🌍", "global": "🌍", "geopolit": "🌍",
    "politic": "🏛️", "government": "🏛️", "policy": "🏛️", "legislation": "🏛️",
    "local": "📍", "longmont": "📍", "colorado": "📍", "community": "📍",
    "weather": "🌤️", "climate": "🌤️", "space weather": "☀️",
    "astronomy": "🌙", "sky": "🌙", "planet": "🌙",
    "stock": "📈", "market": "📈", "economy": "📈", "finance": "📈",
    "energy": "⚡", "grid": "⚡", "datacenter": "⚡", "electric": "⚡",
    "math": "📐", "mathemat": "📐",
    "health": "🏥", "medical": "🏥",
    "culture": "🎭", "art": "🎭", "book": "📚", "history": "📚",
}


def _pick_emoji(title):
    """Return an emoji prefix for a section title, or empty string."""
    lower = title.lower()
    for keyword, emoji in _SECTION_EMOJI.items():
        if keyword in lower:
            return emoji + " "
    return ""


# ---------- source badge colors ----------

_SOURCE_COLORS = {
    "nyt": "#1a1a1a", "new york times": "#1a1a1a",
    "atlantic": "#b41b22", "the atlantic": "#b41b22",
    "nature": "#2a6496",
    "arxiv": "#b31b1b",
    "hacker news": "#ff6600", "hn": "#ff6600",
    "tldr": "#6c5ce7",
    "metafilter": "#006699",
    "reddit": "#ff4500", "r/": "#ff4500",
    "microsoft": "#00a4ef",
    "google": "#4285f4",
    "longmont": "#2d8659",
}


def _source_badge(source_name):
    """Render a small plain pill badge for a source name."""
    if not source_name:
        return ""
    escaped = html_mod.escape(str(source_name))
    color = "#7f8c8d"
    return (
        f'<span style="display:inline-block;background-color:{color};color:#fff;'
        f'font-size:10px;font-weight:600;padding:1px 7px;border-radius:9px;'
        f'font-family:\'Segoe UI\',\'Helvetica Neue\',Arial,sans-serif;'
        f'vertical-align:middle;margin-right:6px;">{escaped}</span>'
    )


# ---------- styles ----------

_FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"

_SECTION_HEADING_STYLE = (
    f"color:#1a1a2e;font-family:{_FONT};"
    "font-size:20px;font-weight:700;margin:24px 0 8px 0;"
)
_SECTION_TEXT_STYLE = (
    f"color:#4a4a5a;font-family:{_FONT};"
    "font-size:14px;line-height:1.5;margin:4px 0 12px 0;font-style:italic;"
)
_CARD_STYLE = (
    "border:1px solid #e8ecf0;border-radius:6px;padding:12px 16px;"
    "margin:8px 0;background-color:#fafbfc;"
)
_CARD_TITLE_STYLE = (
    f"font-family:{_FONT};font-size:15px;font-weight:600;"
    "line-height:1.4;margin:0;"
)
_CARD_META_STYLE = (
    f"color:#7f8c8d;font-family:{_FONT};"
    "font-size:11px;line-height:1.3;margin:4px 0 0 0;"
)
_CARD_SUMMARY_STYLE = (
    f"color:#2c3e50;font-family:{_FONT};"
    "font-size:13px;line-height:1.5;margin:6px 0 0 0;"
)
_A_STYLE = "color:#2980b9;text-decoration:none;"
_P_STYLE = (
    f"color:#2c3e50;font-family:{_FONT};"
    "font-size:14px;line-height:1.6;margin:8px 0;"
)


def _format_date(value):
    """Best-effort formatting of a date value to a clean short string."""
    if not value:
        return ""
    s = str(value).strip()
    from dateutil import parser as dateutil_parser
    try:
        dt = dateutil_parser.parse(s)
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        pass
    return s


# ---------- section renderer (depth 1 = top-level section) ----------

def _render_section(node):
    """Render a top-level section: emoji heading + optional text + article cards."""
    parts = []

    # Section heading with emoji
    emoji = _pick_emoji(node["title"])
    title_html = html_mod.escape(node["title"])
    url = node.get("url") or (node.get("article") or {}).get("url")
    if url:
        title_html = f'<a href="{html_mod.escape(url)}" style="{_A_STYLE}">{title_html}</a>'
    parts.append(f'<h2 style="{_SECTION_HEADING_STYLE}">{emoji}{title_html}</h2>')

    # Optional section-level connector text (italic)
    text = node.get("text")
    if text:
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                parts.append(f'<p style="{_SECTION_TEXT_STYLE}">{html_mod.escape(para)}</p>')

    # If this section itself has article metadata, render as a card
    _render_article_meta(parts, node, text)

    # Children rendered as cards
    for child in node.get("children", []):
        parts.append(_render_card(child))

    return "\n".join(parts)


# ---------- card renderer (depth 2+ = articles/items) ----------

def _render_card(node):
    """Render a child node as a styled card with inline metadata."""
    parts = [f'<div style="{_CARD_STYLE}">']

    # Title line — with source badge and date inline
    title_html = html_mod.escape(node["title"])
    url = node.get("url") or (node.get("article") or {}).get("url")
    if url:
        title_html = f'<a href="{html_mod.escape(url)}" style="{_A_STYLE}">{title_html}</a>'
    parts.append(f'<p style="{_CARD_TITLE_STYLE}">{title_html}</p>')

    # Inline metadata: source badge + date on one line
    article = node.get("article") if isinstance(node.get("article"), dict) else None
    meta_parts = []
    source_name = (article or {}).get("source")
    if source_name:
        meta_parts.append(_source_badge(source_name))
    pub_date = (article or {}).get("published_at")
    if pub_date:
        meta_parts.append(f'<span style="color:#95a5a6;font-size:11px;">{html_mod.escape(_format_date(pub_date))}</span>')
    if meta_parts:
        parts.append(f'<p style="{_CARD_META_STYLE}">{"".join(meta_parts)}</p>')

    # Text / summary (deduplicated)
    text = node.get("text")
    if text:
        clean = " ".join(text.split())
        parts.append(f'<p style="{_CARD_SUMMARY_STYLE}">{html_mod.escape(clean)}</p>')

    summary = (article or {}).get("summary") if article else None
    if summary:
        text_norm = " ".join((text or "").split())
        summary_norm = " ".join(summary.split())
        if summary_norm != text_norm:
            parts.append(f'<p style="{_CARD_SUMMARY_STYLE}">{html_mod.escape(summary)}</p>')

    # Nested children (rare, but supported — renders as sub-cards)
    for child in node.get("children", []):
        parts.append(_render_card(child))

    parts.append("</div>")
    return "\n".join(parts)


def _render_article_meta(parts, node, text):
    """If a node has article metadata at its own level, render it."""
    article = node.get("article") if isinstance(node.get("article"), dict) else None
    if not article:
        return
    meta_parts = []
    if article.get("source"):
        meta_parts.append(_source_badge(article["source"]))
    if article.get("published_at"):
        meta_parts.append(f'<span style="color:#95a5a6;font-size:11px;">{html_mod.escape(_format_date(article["published_at"]))}</span>')
    if meta_parts:
        parts.append(f'<p style="{_CARD_META_STYLE}">{"".join(meta_parts)}</p>')
    summary = article.get("summary")
    if summary:
        text_norm = " ".join((text or "").split())
        summary_norm = " ".join(summary.split())
        if summary_norm != text_norm:
            parts.append(f'<p style="{_P_STYLE}">{html_mod.escape(summary)}</p>')


def _wrap_email_chrome(styled_content, subject):
    """Wrap rendered content in the standard email chrome (header/footer/container)."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="
    background-color: #f0f2f5;
    margin: 0;
    padding: 20px;
    font-family: {_FONT};
">
    <div style="
        max-width: 680px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    ">
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            padding: 24px 28px;
            font-size: 22px;
            font-weight: 700;
            font-family: {_FONT};
            letter-spacing: -0.3px;
        ">
            {html_mod.escape(subject)}
        </div>
        <div style="
            padding: 24px 28px;
            color: #2c3e50;
        ">
            {styled_content}
        </div>
        <div style="
            background-color: #f0f2f5;
            padding: 14px 28px;
            font-size: 11px;
            color: #95a5a6;
            text-align: right;
            font-family: {_FONT};
        ">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>"""


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

    def send_email_json(self, doc: dict, subject: str = None, to_addr: str = None) -> None:
        """Send an email rendered from a structured briefing JSON document.

        Args:
            doc: Validated briefing dict (schema_version 1).
            subject: Email subject (defaults to doc title).
            to_addr: Recipient (defaults to self.to_email).

        Raises:
            ValueError: If the document fails schema validation.
        """
        validate_briefing_json(doc)

        if to_addr is None:
            to_addr = self.to_email
        if subject is None:
            subject = doc.get("title", f"H3LPeR {datetime.now().strftime('%Y-%m-%d')}")

        styled_html = render_briefing_html(doc, subject=subject)

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
