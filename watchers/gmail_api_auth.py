"""gmail_api_auth.py — OAuth 2.0 token management for Gmail API watcher.

Extracted from gmail_api_watcher.py to keep each file under 300 lines (Principle XV).
Handles credential loading, token refresh, and interactive OAuth flow.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate_gmail(
    credentials_path: Path,
    token_path: Path,
) -> Tuple[Optional[object], Optional[str]]:
    """Load or refresh Gmail API credentials and build a service object.

    Returns:
        (service, None) on success.
        (None, error_message) on failure.
    """
    try:
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        import google.auth
        from googleapiclient.discovery import build
    except ImportError:
        return None, (
            "google-auth and google-api-python-client not installed. "
            "Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )

    try:
        creds = None

        if token_path.exists():
            try:
                creds = google.auth.load_credentials_from_file(str(token_path))[0]
            except Exception as e:
                logger.warning(f"Could not load token file: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Gmail token...")
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    return None, (
                        f"credentials.json not found at {credentials_path}. "
                        "Download from Google Cloud Console."
                    )
                logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)

            token_path.write_text(creds.to_json(), encoding="utf-8")

        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API authenticated successfully")
        return service, None

    except Exception as e:
        return None, str(e)
