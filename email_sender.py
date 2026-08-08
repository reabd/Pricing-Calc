"""
Minimal SMTP sender for automated internal notifications (e.g. flagging a
client's rush request to the framing team). Distinct from the Gmail MCP
draft tool used elsewhere in this project — that one only creates drafts
for a human to review and send, and is connected to a different mailbox
(info@reastudio.co.il). This module does a real, immediate send, so it's
only used for internal notifications the studio owner explicitly asked to
be automatic (see studio_operations_and_communication_notes.md §7).

Credentials come from .env (gitignored, never committed):
  SMTP_HOST      e.g. smtp.gmail.com
  SMTP_PORT      e.g. 587
  SMTP_USERNAME  the sending account's address
  SMTP_PASSWORD  an app password (not the account's login password)
  SMTP_FROM      optional; defaults to SMTP_USERNAME
"""
import os
import smtplib
from email.message import EmailMessage


class EmailError(RuntimeError):
    pass


def _config():
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    if not all([host, port, username, password]):
        raise EmailError(
            "SMTP is not configured yet — set SMTP_HOST, SMTP_PORT, "
            "SMTP_USERNAME and SMTP_PASSWORD in .env."
        )
    return host, int(port), username, password


def send_email(to, subject, body):
    host, port, username, password = _config()
    from_addr = os.environ.get("SMTP_FROM") or username

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    except smtplib.SMTPException as e:
        raise EmailError(f"Failed to send email: {e}") from e
    except OSError as e:
        raise EmailError(f"Could not reach SMTP server: {e}") from e
