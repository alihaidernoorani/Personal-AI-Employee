# Contract: Email MCP

**Server**: `mcp-servers/email-mcp/server.py` | **Transport**: stdio | **Runtime**: Python 3.13+
**Status**: ✅ Core implementation exists (SMTP/IMAP). `queue_email` and `flush_queue` tools are **extensions to add** for FR-041 graceful degradation.

## Responsibilities
All Gmail interactions via SMTP (send) and IMAP (search/read), plus local queue management for graceful degradation.

## Tools

### `send_email`
**Input**: `{ to: string, subject: string, body: string, reply_to_id?: string }`
**Output (success)**: `{ message_id: string, status: "sent" }`
**Output (error)**: `{ error: string, retryable: boolean }`
**Rate limit**: Max 10 calls/hour. Returns `{ error: "RATE_LIMIT_EXCEEDED", retryable: false }` on breach.
**Dry-run**: Returns `{ dry_run: true, would_have: "send email to {to}" }`

### `create_draft`
**Input**: `{ to: string, subject: string, body: string }`
**Output (success)**: `{ draft_id: string, status: "draft" }`
**Output (error)**: `{ error: string, retryable: boolean }`

### `search_inbox`
**Input**: `{ query: string, max_results?: number }` (default max_results: 10)
**Output (success)**: `[{ id: string, from: string, subject: string, snippet: string, date: string }]`
**Output (error)**: `{ error: string, retryable: boolean }`

### `queue_email`
**Input**: `{ to: string, subject: string, body: string }`
**Output**: `{ queued: true, queue_position: number }`
**Note**: Used when Gmail API is unavailable. Writes to `scripts/email_outbox_queue.json`.

### `flush_queue`
**Input**: `{}`
**Output**: `{ sent: number, failed: number, errors: [{ to: string, error: string }] }`
**Note**: Drains `email_outbox_queue.json`. Called by orchestrator on Email MCP restoration.

## Error Codes
| Code | Meaning | Retryable |
|---|---|---|
| `AUTH_FAILED` | OAuth2 token expired or revoked | false |
| `RATE_LIMIT_EXCEEDED` | Internal hourly limit hit | false |
| `GMAIL_API_DOWN` | Gmail API unreachable | true |
| `INVALID_RECIPIENT` | Malformed email address | false |
