"""social-mcp — MCP server entry point for social media posting.

All post_* tools require approval_id. DRY_RUN=true (default).
Platform implementations live in handlers/.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

from handlers.linkedin_handler import post_linkedin, get_linkedin_summary
from handlers.facebook_handler import post_facebook
from handlers.instagram_handler import post_instagram
from handlers.twitter_handler import post_twitter

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

VAULT_PATH = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() != "false"

server = Server("social-mcp")


def _log_action(action_type: str, target: str, parameters: dict, approval_status: str, result: dict) -> None:
    try:
        log_dir = VAULT_PATH / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type, "actor": "social-mcp", "target": target,
            "parameters": {k: v for k, v in parameters.items() if k != "approval_id"},
            "approval_status": approval_status,
            "result": result.get("status", result.get("error", "unknown")),
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log: {e}")


def _require_approval(arguments: dict, platform: str) -> dict | None:
    if not arguments.get("approval_id"):
        return {"error": "APPROVAL_REQUIRED", "platform": platform, "retryable": False}
    return None


def _get_post_summary(platform: str, post_id: str) -> dict:
    if DRY_RUN:
        return {"dry_run": True, "platform": platform, "post_id": post_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "content_excerpt": "Dry run", "engagement": {"likes": 0, "shares": 0, "views": 0}}
    if platform == "linkedin":
        return get_linkedin_summary(post_id)
    if platform == "twitter":
        return {"platform": platform, "post_id": post_id, "engagement": None,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "content_excerpt": "", "note": "Engagement requires paid Twitter API tier"}
    return {"platform": platform, "post_id": post_id, "engagement": None,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_excerpt": "", "note": "Engagement retrieval not implemented"}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="post_linkedin", description="Post to LinkedIn. Requires approval_id.",
                   inputSchema={"type": "object", "properties": {"content": {"type": "string"}, "visibility": {"type": "string", "enum": ["PUBLIC", "CONNECTIONS"], "default": "PUBLIC"}, "approval_id": {"type": "string"}}, "required": ["content", "approval_id"]}),
        types.Tool(name="post_facebook", description="Post to Facebook page. Requires approval_id.",
                   inputSchema={"type": "object", "properties": {"content": {"type": "string"}, "page_id": {"type": "string"}, "approval_id": {"type": "string"}}, "required": ["content", "approval_id"]}),
        types.Tool(name="post_instagram", description="Post to Instagram. Requires approval_id.",
                   inputSchema={"type": "object", "properties": {"caption": {"type": "string"}, "image_url": {"type": "string"}, "approval_id": {"type": "string"}}, "required": ["caption", "approval_id"]}),
        types.Tool(name="post_twitter", description="Post a tweet (max 280 chars). Requires approval_id.",
                   inputSchema={"type": "object", "properties": {"content": {"type": "string", "maxLength": 280}, "approval_id": {"type": "string"}}, "required": ["content", "approval_id"]}),
        types.Tool(name="get_post_summary", description="Get engagement summary for a published post.",
                   inputSchema={"type": "object", "properties": {"platform": {"type": "string", "enum": ["linkedin", "facebook", "instagram", "twitter"]}, "post_id": {"type": "string"}}, "required": ["platform", "post_id"]}),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "post_linkedin":
        if err := _require_approval(arguments, "linkedin"):
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = post_linkedin(arguments["content"], arguments.get("visibility", "PUBLIC"), arguments["approval_id"], DRY_RUN)
        _log_action("social_post", "linkedin", arguments, "approved", result)
    elif name == "post_facebook":
        if err := _require_approval(arguments, "facebook"):
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = post_facebook(arguments["content"], arguments.get("page_id", ""), arguments["approval_id"], DRY_RUN)
        _log_action("social_post", "facebook", arguments, "approved", result)
    elif name == "post_instagram":
        if err := _require_approval(arguments, "instagram"):
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = post_instagram(arguments["caption"], arguments.get("image_url"), arguments["approval_id"], DRY_RUN)
        _log_action("social_post", "instagram", arguments, "approved", result)
    elif name == "post_twitter":
        if err := _require_approval(arguments, "twitter"):
            return [types.TextContent(type="text", text=json.dumps(err))]
        result = post_twitter(arguments["content"], arguments["approval_id"], DRY_RUN)
        _log_action("social_post", "twitter", arguments, "approved", result)
    elif name == "get_post_summary":
        result = _get_post_summary(arguments["platform"], arguments["post_id"])
        _log_action("social_summary", arguments["platform"], arguments, "auto", result)
    else:
        raise ValueError(f"Unknown tool: {name}")
    return [types.TextContent(type="text", text=json.dumps(result))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
