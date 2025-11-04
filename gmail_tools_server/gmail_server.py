# gmail_server.py
# ----------------
# Minimal Gmail MCP server (read-only).
#
# Quickstart:
#   pip install mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
#
# Env required:
#   GMAIL_CLIENT_ID=xxx.apps.googleusercontent.com
#   GMAIL_CLIENT_SECRET=xxx
#
# Optional:
#   GMAIL_TOKEN_PATH=./token.json       (default: ./token.json)
#   GMAIL_SCOPES=gmail.readonly         (comma-separated; default: "gmail.readonly")
#
# Run:
#   python gmail_server.py
#
# Then in your MCP client config:
# {
#   "mcpServers": {
#     "gmail": {
#       "command": "python",
#       "args": ["gmail_server.py"],
#       "env": {
#         "GMAIL_CLIENT_ID": "your_client_id.apps.googleusercontent.com",
#         "GMAIL_CLIENT_SECRET": "your_client_secret"
#       }
#     }
#   }
# }

from __future__ import annotations
import os
import json
import base64
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv
load_dotenv()


# ---------- Config ----------
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
SCOPES = [s.strip() for s in os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly").split(",")]

# print(CLIENT_ID)
# print(CLIENT_SECRET)
# print(TOKEN_PATH)
# print(SCOPES)


if not CLIENT_ID or not CLIENT_SECRET:
    print("[Gmail MCP] WARNING: GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET not set. OAuth will fail until provided.")

# ---------- OAuth Helpers ----------
def _credentials() -> Credentials:
    """
    Return a valid Credentials object. Will run a local OAuth flow on first run.
    Stores/refreshes the token at TOKEN_PATH.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"[Gmail MCP] Token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        client_config = {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": ["http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        # Opens a local server + browser for consent the first time
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"[Gmail MCP] Saved token to {TOKEN_PATH}")

    return creds

def _gmail_service():
    creds = _credentials()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

# ---------- Email helpers ----------
HEADER_WANTED = {"From", "To", "Subject", "Date"}

def _pluck_headers(payload_headers: List[Dict[str, str]]) -> Dict[str, str]:
    h = {}
    for item in payload_headers or []:
        name = item.get("name", "")
        val = item.get("value", "")
        if name in HEADER_WANTED:
            h[name] = val
    return h

def _decode_body(payload: Dict[str, Any]) -> str:
    """
    Extract a simple text body from Gmail API message payload.
    Prefers 'text/plain'; falls back to stripping HTML.
    """
    # Single-part
    data = payload.get("body", {}).get("data")
    if data:
        raw = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="ignore")
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/html":
            return _html_to_text(raw)
        return raw

    # Multipart
    parts = payload.get("parts", []) or []
    # Try text/plain first
    for p in parts:
        if p.get("mimeType") == "text/plain":
            d = p.get("body", {}).get("data")
            if d:
                return base64.urlsafe_b64decode(d.encode("utf-8")).decode("utf-8", errors="ignore")
    # Fallback: text/html
    for p in parts:
        if p.get("mimeType") == "text/html":
            d = p.get("body", {}).get("data")
            if d:
                html = base64.urlsafe_b64decode(d.encode("utf-8")).decode("utf-8", errors="ignore")
                return _html_to_text(html)
    return ""

def _html_to_text(html: str) -> str:
    # Very basic HTML to text (enough for summaries)
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>", "\n", text)
    text = re.sub(r"(?is)<.*?>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# ---------- MCP Server ----------
mcp = FastMCP("Gmail MCP")

@mcp.tool()
def get_current_date()->str:
    """_summary_
    Find the current date.
    """

    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool()
def gmail_auth_status() -> Dict[str, Any]:
    """
    Returns whether OAuth is configured and token is present/valid.
    """
    print("Calling gmail_auth_status()")
    try:
        svc = _gmail_service()
        # simple ping by listing labels
        svc.users().labels().list(userId="me").execute()
        ok = True
        msg = "Gmail OAuth is valid."
    except Exception as e:
        ok = False
        msg = f"Gmail OAuth not ready: {e}"
    return {"ok": ok, "message": msg, "token_path": TOKEN_PATH, "scopes": SCOPES}

@mcp.tool()
def gmail_unread_count() -> Dict[str, Any]:
    """
    Returns count of unread messages in INBOX.
    """
    print("Calling gmail_unread_count()")
    svc = _gmail_service()
    res = svc.users().messages().list(userId="me", q="label:inbox is:unread", maxResults=1).execute()
    total = int(res.get("resultSizeEstimate", 0))
    return {"ok": True, "unread_in_inbox": total}

@mcp.tool()
def gmail_list(query: str = "", max_results: int = 10) -> Dict[str, Any]:
    """
    Search and list messages. Returns lightweight cards: id, threadId, headers, snippet.
    - query: Gmail search string (e.g., 'from:amazon subject:invoice newer_than:7d')
    """
    print("Calling gmail_list()")
    svc = _gmail_service()
    result = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    ids = result.get("messages", []) or []

    out = []
    for m in ids:
        msg = svc.users().messages().get(userId="me", id=m["id"], format="metadata", metadataHeaders=list(HEADER_WANTED)).execute()
        headers = _pluck_headers(msg.get("payload", {}).get("headers", []))
        snippet = msg.get("snippet", "") or ""
        out.append({
            "id": msg["id"],
            "threadId": msg.get("threadId"),
            "headers": headers,
            "snippet": snippet,
        })

    return {"ok": True, "query": query, "count": len(out), "messages": out}

@mcp.tool()
def gmail_read(message_id: str) -> Dict[str, Any]:
    """
    Read a single message by id. Returns headers + best-effort text body.
    """
    print("Calling gmail_read()")
    svc = _gmail_service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = _pluck_headers(payload.get("headers", []))
    text = _decode_body(payload)
    return {
        "ok": True,
        "id": msg["id"],
        "threadId": msg.get("threadId"),
        "labels": msg.get("labelIds", []),
        "headers": headers,
        "snippet": msg.get("snippet", ""),
        "body_text": text,
        "size_estimate": msg.get("sizeEstimate", 0),
        "internalDate": msg.get("internalDate")  # ms since epoch
    }

if __name__ == "__main__":
    # stdio so MCP clients can attach
    mcp.run(transport="stdio")


