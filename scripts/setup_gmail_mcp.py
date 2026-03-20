"""
One-time OAuth 2.0 setup for the email-mcp server.

Run this once to authorize the Gmail API with send + compose + read scopes.
The token is saved to .gmail_mcp_token.json and auto-refreshes thereafter.

Usage (PowerShell):
  python scripts/setup_gmail_mcp.py

Requires:
  - credentials.json in the project root (downloaded from Google Cloud Console)
  - pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / ".gmail_mcp_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("ERROR: Missing Google libraries. Run:")
        print("  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    creds = None

    # Load existing token if present
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        print(f"Token already valid at {TOKEN_FILE}")
        print("Scopes:", creds.scopes)
        return

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired token...")
        creds.refresh(Request())
    else:
        print("Opening browser for Gmail authorization...")
        print(f"Credentials: {CREDENTIALS_FILE}")
        print(f"Scopes: {SCOPES}\n")
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"\nToken saved to {TOKEN_FILE}")
    print("The email-mcp server is now authorized and ready.")
    print("\nNext: Restart Claude Code to load the MCP server.")


if __name__ == "__main__":
    main()
