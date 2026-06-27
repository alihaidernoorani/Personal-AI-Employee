"""twitter_handler.py — Twitter/X posting handler via API v2 (OAuth 1.0a)."""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def post_twitter(content: str, approval_id: str, dry_run: bool) -> dict:
    if len(content) > 280:
        return {"error": "CONTENT_TOO_LONG", "max_chars": 280, "provided": len(content),
                "platform": "twitter", "retryable": False}
    if dry_run:
        return {"dry_run": True, "would_have": f"tweet: {content[:50]}"}
    try:
        import requests
        from requests_oauthlib import OAuth1
    except ImportError as e:
        return {"error": f"Missing dependency: {e}. Run: pip install requests requests-oauthlib",
                "platform": "twitter", "retryable": False}
    api_key = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    if not all([api_key, api_secret, access_token, access_token_secret]):
        return {"error": "AUTH_FAILED", "detail": "TWITTER_API_KEY/SECRET/ACCESS_TOKEN/ACCESS_TOKEN_SECRET not configured",
                "platform": "twitter", "retryable": False}
    try:
        auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
        resp = requests.post("https://api.twitter.com/2/tweets", auth=auth,
                             json={"text": content}, timeout=15)
        if resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "twitter", "retryable": False}
        if resp.status_code == 429:
            return {"error": "RATE_LIMITED", "platform": "twitter", "retryable": True}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "twitter", "retryable": True}
        resp.raise_for_status()
        tweet_id = resp.json().get("data", {}).get("id", "unknown")
        return {"tweet_id": tweet_id, "url": f"https://x.com/i/web/status/{tweet_id}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "twitter", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "twitter", "retryable": True}
