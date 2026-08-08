"""
Reads the studio's Gmail inbox via IMAP (Google App Password auth — same
credential as email_sender.py's SMTP, since a Gmail App Password grants both)
to find new, unanswered client emails, and can append a draft reply directly
into the mailbox's Drafts folder. Used by the background poller in app.py —
see studio_operations_and_communication_notes.md §9 for the full design.

Never sends anything. The only mailbox-mutating operations here are:
  - appending a draft to [Gmail]/Drafts
  - applying a custom label to mark a message as already reviewed (so the
    poller doesn't re-process it every cycle) — deliberately NOT touching
    the \\Seen flag, since staff rely on unread/read state for their own
    workflow and this bot's involvement shouldn't interfere with that.
"""
import email
import imaplib
import os
import re
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime

IMAP_HOST = "imap.gmail.com"
REVIEWED_LABEL = "Claude/Reviewed"


class ImapError(RuntimeError):
    pass


def _credentials():
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    if not username or not password:
        raise ImapError("SMTP_USERNAME / SMTP_PASSWORD are not set (add them to .env)")
    return username, password


def _connect():
    username, password = _credentials()
    try:
        conn = imaplib.IMAP4_SSL(IMAP_HOST)
        conn.login(username, password)
    except imaplib.IMAP4.error as e:
        raise ImapError(f"IMAP login failed: {e}") from e
    except OSError as e:
        raise ImapError(f"Could not reach {IMAP_HOST}: {e}") from e
    return conn


def _decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _plaintext_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
        # fall back to the first text/html part, stripped, if no plaintext part exists
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                html = part.get_payload(decode=True).decode(charset, errors="replace")
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""


def _is_already_reviewed(conn, uid):
    typ, data = conn.uid("FETCH", uid, "(X-GM-LABELS)")
    if typ != "OK" or not data or not data[0]:
        return False
    raw = data[0].decode("utf-8", errors="replace") if isinstance(data[0], bytes) else str(data[0])
    return REVIEWED_LABEL in raw


def mark_reviewed(uid):
    """Applies the tracking label without touching \\Seen — a separate,
    short-lived connection since this is called after fetch_unanswered()'s
    connection may already be closed."""
    conn = _connect()
    try:
        conn.select("INBOX")
        conn.uid("STORE", uid, "+X-GM-LABELS", f'("{REVIEWED_LABEL}")')
    finally:
        conn.logout()


def fetch_unanswered_inbox_emails(limit=25):
    """
    Returns a list of candidate emails: unread, in INBOX, not already
    labeled REVIEWED_LABEL, and — critically — with no later message from
    us in the same Gmail thread (i.e. genuinely still waiting on a reply,
    not just a thread where staff happened to leave an old message unread
    after already answering a newer one).

    Each item: {uid, thread_id, message_id, from_name, from_email, subject,
    date, body, in_reply_to_message_id}
    """
    conn = _connect()
    try:
        conn.select("INBOX")
        typ, data = conn.uid("SEARCH", None, "UNSEEN")
        if typ != "OK" or not data or not data[0]:
            return []
        uids = data[0].split()[-limit:]  # newest first isn't guaranteed by SEARCH order; caller doesn't need strict order

        candidates = []
        for uid in uids:
            if _is_already_reviewed(conn, uid):
                continue

            typ, msg_data = conn.uid("FETCH", uid, "(RFC822 X-GM-THRID)")
            if typ != "OK" or not msg_data or msg_data[0] is None:
                continue
            raw_headers = msg_data[0][0].decode("utf-8", errors="replace") if isinstance(msg_data[0], tuple) else ""
            thrid_match = re.search(r"X-GM-THRID (\d+)", raw_headers)
            thread_id = thrid_match.group(1) if thrid_match else None

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_name, from_email = parseaddr(_decode(msg.get("From")))
            subject = _decode(msg.get("Subject"))
            message_id = msg.get("Message-ID")
            try:
                date = parsedate_to_datetime(msg.get("Date"))
            except (TypeError, ValueError):
                date = None
            body = _plaintext_body(msg).strip()

            if thread_id and date and _we_already_replied_after(conn, thread_id, date):
                continue

            candidates.append({
                "uid": uid.decode() if isinstance(uid, bytes) else uid,
                "thread_id": thread_id,
                "message_id": message_id,
                "from_name": from_name,
                "from_email": from_email,
                "subject": subject,
                "date": date,
                "body": body[:4000],  # cap — this only feeds an LLM prompt, not a full archive
            })
        return candidates
    finally:
        conn.logout()


def _we_already_replied_after(conn, thread_id, after_date):
    """Checks [Gmail]/Sent Mail for a message in the same thread sent after
    `after_date` — if found, this inbound message has already been handled
    (even if some older message in the same thread is still marked unread)."""
    try:
        typ, _ = conn.select('"[Gmail]/Sent Mail"')
        if typ != "OK":
            return False
        typ, data = conn.uid("SEARCH", None, "X-GM-THRID", thread_id)
        if typ != "OK" or not data or not data[0]:
            return False
        for uid in data[0].split():
            typ, msg_data = conn.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (DATE)])")
            if typ != "OK" or not msg_data or msg_data[0] is None:
                continue
            header_bytes = msg_data[0][1] if isinstance(msg_data[0], tuple) else b""
            date_match = re.search(rb"Date:\s*(.+)", header_bytes)
            if not date_match:
                continue
            try:
                sent_date = parsedate_to_datetime(date_match.group(1).decode("utf-8", errors="replace").strip())
            except (TypeError, ValueError):
                continue
            if sent_date > after_date:
                return True
        return False
    finally:
        conn.select("INBOX")


def append_draft_reply(original, reply_subject, reply_body):
    """
    Builds a proper threaded reply (In-Reply-To / References set so Gmail
    shows it in the same conversation) and APPENDs it to [Gmail]/Drafts.
    Never sends. `original` is one of the dicts returned by
    fetch_unanswered_inbox_emails().
    """
    username, _ = _credentials()
    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = original["from_email"]
    msg["Subject"] = reply_subject
    if original.get("message_id"):
        msg["In-Reply-To"] = original["message_id"]
        msg["References"] = original["message_id"]
    msg.set_content(reply_body)

    conn = _connect()
    try:
        conn.append('"[Gmail]/Drafts"', "", imaplib.Time2Internaldate(__import__("time").time()), msg.as_bytes())
    finally:
        conn.logout()
