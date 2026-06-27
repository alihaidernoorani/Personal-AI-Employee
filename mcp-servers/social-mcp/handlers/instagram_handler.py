"""instagram_handler.py — Instagram posting handler via Graph API."""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def post_instagram(caption: str, image_url: str | None, approval_id: str, dry_run: bool) -> dict:
    if dry_run:
        return {"dry_run": True, "would_have": f"post to instagram: {caption[:50]}"}
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed", "platform": "instagram", "retryable": False}
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
    if not token:
        return {"error": "AUTH_FAILED", "platform": "instagram", "retryable": False}
    if not ig_user_id:
        return {"error": "INSTAGRAM_USER_ID not configured", "platform": "instagram", "retryable": False}
    if not image_url:
        return {"error": "image_url required — Instagram Graph API does not support text-only posts",
                "platform": "instagram", "retryable": False}
    try:
        container_payload = {"caption": caption, "image_url": image_url,
                             "media_type": "IMAGE", "access_token": token}
        container_resp = requests.post(f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
                                       params=container_payload, timeout=15)
        if container_resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "instagram", "retryable": False}
        if container_resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "instagram", "retryable": True}
        if not container_resp.ok:
            return {"error": f"FB_API_{container_resp.status_code}", "detail": container_resp.json(),
                    "platform": "instagram", "retryable": False}
        container_id = container_resp.json().get("id")
        publish_resp = requests.post(f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish",
                                     params={"creation_id": container_id, "access_token": token}, timeout=15)
        if not publish_resp.ok:
            return {"error": f"FB_API_{publish_resp.status_code}", "detail": publish_resp.json(),
                    "platform": "instagram", "retryable": False}
        post_id = publish_resp.json().get("id", "unknown")
        return {"post_id": post_id, "url": f"https://www.instagram.com/p/{post_id}/",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "instagram", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "instagram", "retryable": True}
