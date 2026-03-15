# email-mcp Registration

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "email-mcp": {
    "command": "python",
    "args": ["/ABSOLUTE/PATH/TO/mcp-servers/email-mcp/server.py"],
    "env": {
      "GMAIL_EMAIL": "${GMAIL_EMAIL}",
      "GMAIL_APP_PASSWORD": "${GMAIL_APP_PASSWORD}",
      "VAULT_PATH": "${VAULT_PATH}",
      "DRY_RUN": "${DRY_RUN}"
    }
  }
}
```

Replace `/ABSOLUTE/PATH/TO/` with the actual path to this repository.

After registration: `claude mcp list` should show `email-mcp`.

## Prerequisites

1. Enable IMAP in Gmail: Settings > See all settings > Forwarding and POP/IMAP > Enable IMAP
2. Create a Gmail App Password: Google Account > Security > 2-Step Verification > App passwords
3. Set `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` in your `.env` file

## Tools

| Tool | Description |
|------|-------------|
| `send_email` | Send email via Gmail SMTP (gated by DRY_RUN) |
| `draft_reply` | Save draft to Gmail Drafts folder |
| `search_inbox` | Search Gmail INBOX with IMAP query |
