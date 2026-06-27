"""linkedin_handler.py — LinkedIn posting handler."""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def post_linkedin(content: str, visibility: str, approval_id: str, dry_run: bool) -> dict:
    if dry_run:
        return {"dry_run": True, "would_have": f"post to linkedin: {content[:50]}"}
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed", "platform": "linkedin", "retryable": False}
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
    try:
        me_resp = requests.get("https://api.linkedin.com/v2/me",
                               headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if me_resp.status_code == 401:
            return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
        me_resp.raise_for_status()
        author_urn = f"urn:li:person:{me_resp.json()['id']}"
        payload = {
            "author": author_urn, "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content}, "shareMediaCategory": "NONE"}},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        resp = requests.post("https://api.linkedin.com/v2/ugcPosts",
                             headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                      "X-Restli-Protocol-Version": "2.0.0"},
                             json=payload, timeout=15)
        if resp.status_code == 401:
            return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
        if resp.status_code == 422:
            return {"error": "CONTENT_POLICY", "platform": "linkedin", "retryable": False}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "linkedin", "retryable": True}
        resp.raise_for_status()
        post_id = resp.headers.get("X-RestLi-Id", resp.json().get("id", "unknown"))
        return {"post_id": post_id, "url": f"https://www.linkedin.com/feed/update/{post_id}/",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "linkedin", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "linkedin", "retryable": True}


def get_linkedin_summary(post_id: str) -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    try:
        import requests
        if not token:
            return {"platform": "linkedin", "post_id": post_id, "engagement": None, "note": "token not configured",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "content_excerpt": ""}
        resp = requests.get(f"https://api.linkedin.com/v2/socialActions/{post_id}",
                            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code != 200:
            return {"error": "PLATFORM_API_DOWN", "platform": "linkedin", "retryable": True}
        data = resp.json()
        return {"platform": "linkedin", "post_id": post_id, "content_excerpt": "",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "engagement": {"likes": data.get("likesSummary", {}).get("totalLikes", 0),
                               "shares": data.get("shareStatistics", {}).get("shareCount", 0),
                               "views": data.get("shareStatistics", {}).get("impressionCount", 0)}}
    except Exception as e:
        return {"error": str(e), "platform": "linkedin", "retryable": True}
