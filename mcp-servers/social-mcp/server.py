"""social-mcp — Python MCP server (stdio transport) for social media posting.

Tools:
  - post_linkedin(content, visibility?, approval_id)
  - post_facebook(content, page_id?, approval_id)
  - post_instagram(caption, image_url?, approval_id)
  - post_twitter(content, approval_id)
  - get_post_summary(platform, post_id)

All post_* tools require approval_id. No http:// URLs used — HTTPS only.
DRY_RUN=true (default) — no real posts sent during development.
"""

import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

# Credentials from environment
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

server = Server("social-mcp")


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def _log_action(action_type: str, target: str, parameters: dict, approval_status: str, result: dict) -> None:
    try:
        log_dir = VAULT_PATH / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "actor": "social-mcp",
            "target": target,
            "parameters": {k: v for k, v in parameters.items() if k != "approval_id"},
            "approval_status": approval_status,
            "result": result.get("status", result.get("error", "unknown")),
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log: {e}")


# ---------------------------------------------------------------------------
# Approval gate
# ---------------------------------------------------------------------------

def _require_approval(arguments: dict, platform: str) -> dict | None:
    """Return error dict if approval_id missing, else None."""
    if not arguments.get("approval_id"):
        return {"error": "APPROVAL_REQUIRED", "platform": platform, "retryable": False}
    return None


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _post_linkedin(content: str, visibility: str, approval_id: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "would_have": f"post to linkedin: {content[:50]}"}
    if not REQUESTS_AVAILABLE:
        return {"error": "requests library not installed", "platform": "linkedin", "retryable": False}
    if not LINKEDIN_ACCESS_TOKEN:
        return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
    try:
        # Get author URN first
        me_resp = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
            timeout=15,
        )
        if me_resp.status_code == 401:
            return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
        me_resp.raise_for_status()
        author_urn = f"urn:li:person:{me_resp.json()['id']}"

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code == 401:
            return {"error": "AUTH_FAILED", "platform": "linkedin", "retryable": False}
        if resp.status_code == 422:
            return {"error": "CONTENT_POLICY", "platform": "linkedin", "retryable": False}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "linkedin", "retryable": True}
        resp.raise_for_status()
        post_id = resp.headers.get("X-RestLi-Id", resp.json().get("id", "unknown"))
        return {
            "post_id": post_id,
            "url": f"https://www.linkedin.com/feed/update/{post_id}/",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "linkedin", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "linkedin", "retryable": True}


def _post_facebook(content: str, page_id: str, approval_id: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "would_have": f"post to facebook: {content[:50]}"}
    if not REQUESTS_AVAILABLE:
        return {"error": "requests library not installed", "platform": "facebook", "retryable": False}
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        return {"error": "AUTH_FAILED", "platform": "facebook", "retryable": False}
    pid = page_id or FACEBOOK_PAGE_ID
    if not pid:
        return {"error": "FACEBOOK_PAGE_ID not configured", "platform": "facebook", "retryable": False}
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{pid}/feed",
            params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN},
            json={"message": content},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "facebook", "retryable": False}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "facebook", "retryable": True}
        resp.raise_for_status()
        post_id = resp.json().get("id", "unknown")
        return {
            "post_id": post_id,
            "url": f"https://www.facebook.com/{post_id}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "facebook", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "facebook", "retryable": True}


def _post_instagram(caption: str, image_url: str | None, approval_id: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "would_have": f"post to instagram: {caption[:50]}"}
    if not REQUESTS_AVAILABLE:
        return {"error": "requests library not installed", "platform": "instagram", "retryable": False}
    if not INSTAGRAM_ACCESS_TOKEN:
        return {"error": "AUTH_FAILED", "platform": "instagram", "retryable": False}
    # Instagram Graph API: create media container then publish
    try:
        ig_user_id = os.getenv("INSTAGRAM_USER_ID", "")
        if not ig_user_id:
            return {"error": "INSTAGRAM_USER_ID not configured", "platform": "instagram", "retryable": False}
        container_payload: dict = {"caption": caption, "access_token": INSTAGRAM_ACCESS_TOKEN}
        if image_url:
            container_payload["image_url"] = image_url
            container_payload["media_type"] = "IMAGE"
        else:
            container_payload["media_type"] = "TEXT"

        container_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_user_id}/media",
            params=container_payload,
            timeout=15,
        )
        if container_resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "instagram", "retryable": False}
        if container_resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "instagram", "retryable": True}
        container_resp.raise_for_status()
        container_id = container_resp.json().get("id")

        publish_resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish",
            params={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
            timeout=15,
        )
        publish_resp.raise_for_status()
        post_id = publish_resp.json().get("id", "unknown")
        return {
            "post_id": post_id,
            "url": f"https://www.instagram.com/p/{post_id}/",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "instagram", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "instagram", "retryable": True}


def _post_twitter(content: str, approval_id: str) -> dict:
    if len(content) > 280:
        return {
            "error": "CONTENT_TOO_LONG",
            "max_chars": 280,
            "provided": len(content),
            "platform": "twitter",
            "retryable": False,
        }
    if DRY_RUN:
        return {"dry_run": True, "would_have": f"tweet: {content[:50]}"}
    if not REQUESTS_AVAILABLE:
        return {"error": "requests library not installed", "platform": "twitter", "retryable": False}
    if not TWITTER_BEARER_TOKEN:
        return {"error": "AUTH_FAILED", "platform": "twitter", "retryable": False}
    try:
        resp = requests.post(
            "https://api.twitter.com/2/tweets",
            headers={
                "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"text": content},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"error": "AUTH_FAILED", "platform": "twitter", "retryable": False}
        if resp.status_code == 429:
            return {"error": "RATE_LIMITED", "platform": "twitter", "retryable": True}
        if resp.status_code >= 500:
            return {"error": "PLATFORM_API_DOWN", "platform": "twitter", "retryable": True}
        resp.raise_for_status()
        tweet_id = resp.json().get("data", {}).get("id", "unknown")
        return {
            "tweet_id": tweet_id,
            "url": f"https://twitter.com/i/web/status/{tweet_id}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except requests.ConnectionError:
        return {"error": "PLATFORM_API_DOWN", "platform": "twitter", "retryable": True}
    except Exception as e:
        return {"error": str(e), "platform": "twitter", "retryable": True}


def _get_post_summary(platform: str, post_id: str) -> dict:
    if DRY_RUN:
        return {
            "dry_run": True,
            "platform": platform,
            "post_id": post_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_excerpt": "Dry run — no content available",
            "engagement": {"likes": 0, "shares": 0, "views": 0},
        }
    # Twitter engagement requires paid API tier
    if platform == "twitter":
        return {
            "platform": platform,
            "post_id": post_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_excerpt": "",
            "engagement": None,
            "note": "Engagement data requires paid Twitter API tier",
        }
    # LinkedIn engagement
    if platform == "linkedin":
        if not LINKEDIN_ACCESS_TOKEN or not REQUESTS_AVAILABLE:
            return {
                "platform": platform,
                "post_id": post_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "content_excerpt": "",
                "engagement": None,
                "note": "LinkedIn access token not configured",
            }
        try:
            resp = requests.get(
                f"https://api.linkedin.com/v2/socialActions/{post_id}",
                headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
                timeout=15,
            )
            if resp.status_code != 200:
                return {"error": "PLATFORM_API_DOWN", "platform": platform, "retryable": True}
            data = resp.json()
            return {
                "platform": platform,
                "post_id": post_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "content_excerpt": "",
                "engagement": {
                    "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                    "shares": data.get("shareStatistics", {}).get("shareCount", 0),
                    "views": data.get("shareStatistics", {}).get("impressionCount", 0),
                },
            }
        except Exception as e:
            return {"error": str(e), "platform": platform, "retryable": True}
    # Facebook/Instagram basic engagement
    if platform in ("facebook", "instagram"):
        return {
            "platform": platform,
            "post_id": post_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_excerpt": "",
            "engagement": None,
            "note": "Engagement retrieval not implemented for this platform tier",
        }
    return {"error": f"Unknown platform: {platform}", "platform": platform, "retryable": False}


# ---------------------------------------------------------------------------
# MCP tool registry
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="post_linkedin",
            description="Post to LinkedIn. Requires approval_id. Respects DRY_RUN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"},
                    "approval_id": {"type": "string"},
                },
                "required": ["content", "approval_id"],
            },
        ),
        types.Tool(
            name="post_facebook",
            description="Post to Facebook page. Requires approval_id. Respects DRY_RUN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "page_id": {"type": "string"},
                    "approval_id": {"type": "string"},
                },
                "required": ["content", "approval_id"],
            },
        ),
        types.Tool(
            name="post_instagram",
            description="Post to Instagram. Requires approval_id. Respects DRY_RUN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string"},
                    "image_url": {"type": "string"},
                    "approval_id": {"type": "string"},
                },
                "required": ["caption", "approval_id"],
            },
        ),
        types.Tool(
            name="post_twitter",
            description="Post a tweet (max 280 chars). Requires approval_id. Respects DRY_RUN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "maxLength": 280},
                    "approval_id": {"type": "string"},
                },
                "required": ["content", "approval_id"],
            },
        ),
        types.Tool(
            name="get_post_summary",
            description="Get engagement summary for a published post.",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "enum": ["linkedin", "facebook", "instagram", "twitter"]},
                    "post_id": {"type": "string"},
                },
                "required": ["platform", "post_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "post_linkedin":
        err = _require_approval(arguments, "linkedin")
        if err:
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = _post_linkedin(
            content=arguments["content"],
            visibility=arguments.get("visibility", "PUBLIC"),
            approval_id=arguments["approval_id"],
        )
        _log_action("social_post", "linkedin", arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "post_facebook":
        err = _require_approval(arguments, "facebook")
        if err:
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = _post_facebook(
            content=arguments["content"],
            page_id=arguments.get("page_id", ""),
            approval_id=arguments["approval_id"],
        )
        _log_action("social_post", "facebook", arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "post_instagram":
        err = _require_approval(arguments, "instagram")
        if err:
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = _post_instagram(
            caption=arguments["caption"],
            image_url=arguments.get("image_url"),
            approval_id=arguments["approval_id"],
        )
        _log_action("social_post", "instagram", arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "post_twitter":
        err = _require_approval(arguments, "twitter")
        if err:
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = _post_twitter(
            content=arguments["content"],
            approval_id=arguments["approval_id"],
        )
        _log_action("social_post", "twitter", arguments, "approved", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "get_post_summary":
        result = _get_post_summary(
            platform=arguments["platform"],
            post_id=arguments["post_id"],
        )
        _log_action("social_summary", arguments["platform"], arguments, "auto", result)
        return [types.TextContent(type="text", text=json.dumps(result))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
