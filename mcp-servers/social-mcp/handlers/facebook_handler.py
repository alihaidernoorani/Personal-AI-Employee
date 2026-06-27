"""facebook_handler.py — Facebook posting handler."""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def post_facebook(content: str, page_id: str, approval_id: str, dry_run: bool) -> dict:
    if dry_run:
        return {"dry_run": True, "would_have": f"post to facebook: {content[:50]}"}
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed", "platform": "facebook", "retryable": False}
    token = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    if not token:
        return {"error": "AUTH_FAILED", "platform": "facebook", "retryable": False}
    pid = page_id or os.getenv("FACEBOOK_PAGE_ID", "")
    if not pid:
        return {"error": "FACEBOOK_PAGE_ID not configured", "platform": "facebook", "retryable": False}
    try:
        resp = requests.post(f"https://graph.facebook.com/v20.0/{pid}/feed",
                             params={"access_token": token}, json={"message": content}, timeout=15)
        if resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "facebook", "retryable": False}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "facebook", "retryable": True}
        resp.raise_for_status()
        post_id = resp.json().get("id", "unknown")
        return {"post_id": post_id, "url": f"https://www.facebook.com/{post_id}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "facebook", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "facebook", "retryable": True}
