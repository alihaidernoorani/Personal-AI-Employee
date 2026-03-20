"""
LinkedIn API v2 — Post to company page or personal profile.

Auth flow (first run):
  python scripts/linkedin_post.py --auth

Post a message:
  python scripts/linkedin_post.py --post "Your message here"

Token is stored in .linkedin_token.json (gitignored).
"""

import argparse
import json
import os
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / ".linkedin_token.json"

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
COMPANY_URN = os.getenv("COMPANY_URN", "")          # urn:li:organization:XXXXXXX
ACCESS_TOKEN_ENV = os.getenv("LINKEDIN_ACCESS_TOKEN", "")  # static token from .env
REDIRECT_URI = "http://localhost:8765/callback"

SCOPES = "w_member_social w_organization_social r_organization_social"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
UGC_URL = "https://api.linkedin.com/v2/ugcPosts"

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


# ── Token helpers ──────────────────────────────────────────────────────────────

def _load_token() -> dict | None:
    try:
        return json.loads(TOKEN_FILE.read_text())
    except Exception:
        return None


def _save_token(token: dict):
    TOKEN_FILE.write_text(json.dumps(token, indent=2))
    print(f"Token saved to {TOKEN_FILE}")


def _token_is_valid(token: dict) -> bool:
    expires_at = token.get("expires_at", 0)
    return bool(token.get("access_token")) and datetime.now(timezone.utc).timestamp() < expires_at


# ── OAuth flow ─────────────────────────────────────────────────────────────────

_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    """Tiny local HTTP server to capture the OAuth callback code."""

    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]

        if code:
            _auth_code = code
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Authorised! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Error: {error}</h2>".encode())

    def log_message(self, *_):
        pass  # suppress request logs


def authenticate() -> dict:
    """
    Full OAuth 2.0 authorization code flow.
    Opens the browser, starts a local server to capture the code,
    exchanges it for tokens, and saves them to TOKEN_FILE.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit("ERROR: LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in .env")

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "linkedin_auth",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    # Start local callback server in background thread
    server = HTTPServer(("localhost", 8765), _CallbackHandler)
    thread = Thread(target=server.handle_request, daemon=True)
    thread.start()

    print(f"\nOpening browser for LinkedIn authorisation...\n{url}\n")
    webbrowser.open(url)
    thread.join(timeout=120)

    global _auth_code
    if not _auth_code:
        sys.exit("ERROR: No authorisation code received within 120 seconds.")

    # Exchange code for tokens
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    token_data = resp.json()

    # Store with expiry timestamp
    token_data["expires_at"] = (
        datetime.now(timezone.utc).timestamp() + token_data.get("expires_in", 5184000)
    )
    _save_token(token_data)
    print("Authentication successful.")
    return token_data


def get_access_token() -> str:
    """
    Return a valid access token using this priority order:
      1. LINKEDIN_ACCESS_TOKEN in .env  (static token — no expiry check)
      2. Saved .linkedin_token.json     (OAuth flow token with expiry)
      3. Full OAuth flow                (opens browser, saves new token)
    """
    if ACCESS_TOKEN_ENV:
        return ACCESS_TOKEN_ENV

    token = _load_token()
    if token and _token_is_valid(token):
        return token["access_token"]

    print("No valid token found. Starting authentication flow...")
    token = authenticate()
    return token["access_token"]


# ── LinkedIn API ───────────────────────────────────────────────────────────────

def get_author_urn(access_token: str) -> str:
    """
    Return the author URN to post as.
    Prefers COMPANY_URN from .env; falls back to the authenticated member URN.

    Uses /v2/userinfo (OIDC) because /v2/me requires r_liteprofile scope.
    The 'sub' claim from userinfo is the LinkedIn member ID usable as urn:li:person:<sub>.
    """
    if COMPANY_URN:
        return COMPANY_URN

    resp = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    sub = resp.json().get("sub", "")
    if not sub:
        sys.exit("ERROR: Could not resolve member ID from /v2/userinfo. Check token scopes.")
    return f"urn:li:person:{sub}"


def post_to_linkedin(message_text: str) -> dict:
    """
    Publish a text post to LinkedIn via API v2 UGC Posts endpoint.

    Args:
        message_text: The post content (plain text, up to ~3000 chars).

    Returns:
        dict with keys: success (bool), post_id (str|None), url (str|None), error (str|None)
    """
    if not message_text.strip():
        return {"success": False, "error": "message_text is empty"}

    if DRY_RUN:
        print(f"[DRY RUN] Would post to LinkedIn:\n{message_text[:200]}...")
        return {"success": True, "post_id": "dry-run", "url": None, "dry_run": True}

    access_token = get_access_token()
    author_urn = get_author_urn(access_token)

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    resp = requests.post(UGC_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code == 201:
        post_id = resp.headers.get("x-restli-id", "")
        post_url = f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else None
        print(f"Posted successfully. ID: {post_id}")
        return {"success": True, "post_id": post_id, "url": post_url, "error": None}

    return {
        "success": False,
        "post_id": None,
        "url": None,
        "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn API v2 poster")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--auth", action="store_true", help="Run OAuth flow to get access token")
    group.add_argument("--post", metavar="TEXT", help="Post text to LinkedIn")
    group.add_argument("--token-info", action="store_true", help="Show current token status")

    args = parser.parse_args()

    if args.auth:
        authenticate()

    elif args.token_info:
        if ACCESS_TOKEN_ENV:
            print(f"Source : LINKEDIN_ACCESS_TOKEN in .env")
            print(f"Token  : {ACCESS_TOKEN_ENV[:20]}...{ACCESS_TOKEN_ENV[-6:]}")
            print("Note   : Static token — no expiry tracked. Rotate manually when expired.")
        else:
            token = _load_token()
            if not token:
                print("No token found. Run: python scripts/linkedin_post.py --auth")
            else:
                valid = _token_is_valid(token)
                expires = datetime.fromtimestamp(token.get("expires_at", 0), tz=timezone.utc)
                print(f"Source : .linkedin_token.json")
                print(f"Valid  : {valid}")
                print(f"Expires: {expires.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"Scopes : {token.get('scope', 'unknown')}")

    elif args.post:
        result = post_to_linkedin(args.post)
        if result["success"]:
            print(f"Success: {result}")
            sys.exit(0)
        else:
            print(f"Failed: {result['error']}")
            sys.exit(1)
