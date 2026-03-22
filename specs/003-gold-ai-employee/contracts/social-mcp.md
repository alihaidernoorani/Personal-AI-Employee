# Contract: Social MCP

**Server**: `mcp-servers/social-mcp/server.py` | **Transport**: stdio | **Runtime**: Python 3.13+
**Status**: ❌ To build.

## Responsibilities
Post publication and activity summary generation for LinkedIn, Facebook, Instagram, and Twitter/X.

## Tools

### `post_linkedin`
**Input**: `{ content: string, visibility?: "PUBLIC" | "CONNECTIONS" }`
**Output (success)**: `{ post_id: string, url: string, timestamp: string }`
**Output (error)**: `{ error: string, platform: "linkedin", retryable: boolean }`

### `post_facebook`
**Input**: `{ content: string, page_id: string }`
**Output (success)**: `{ post_id: string, url: string, timestamp: string }`
**Output (error)**: `{ error: string, platform: "facebook", retryable: boolean }`

### `post_instagram`
**Input**: `{ caption: string, image_url?: string }`
**Output (success)**: `{ post_id: string, url: string, timestamp: string }`
**Output (error)**: `{ error: string, platform: "instagram", retryable: boolean }`

### `post_twitter`
**Input**: `{ content: string }` (max 280 chars enforced by server)
**Output (success)**: `{ tweet_id: string, url: string, timestamp: string }`
**Output (error)**: `{ error: string, platform: "twitter", retryable: boolean }`

### `get_post_summary`
**Input**: `{ platform: "linkedin" | "facebook" | "instagram" | "twitter", post_id: string }`
**Output (success)**:
```json
{
  "platform": "linkedin",
  "post_id": "...",
  "timestamp": "ISO-8601Z",
  "content_excerpt": "First 100 chars...",
  "engagement": {
    "likes": 12,
    "shares": 3,
    "views": 240
  }
}
```
**Output (engagement unavailable)**:
```json
{
  "platform": "twitter",
  "post_id": "...",
  "timestamp": "ISO-8601Z",
  "content_excerpt": "...",
  "engagement": null,
  "note": "Engagement data requires paid Twitter API tier"
}
```
**Output (error)**: `{ error: string, platform: string, retryable: boolean }`

## Approval Requirement
All `post_*` tools require a valid `approval_id` parameter. Calls without it return:
`{ error: "APPROVAL_REQUIRED", retryable: false }`

## Error Codes
| Code | Meaning | Retryable |
|---|---|---|
| `APPROVAL_REQUIRED` | No approval_id provided | false |
| `AUTH_FAILED` | API token expired or revoked | false |
| `PLATFORM_API_DOWN` | Platform API unreachable | true |
| `CONTENT_POLICY` | Content rejected by platform | false |
| `RATE_LIMITED` | Platform rate limit hit | true (after backoff) |
