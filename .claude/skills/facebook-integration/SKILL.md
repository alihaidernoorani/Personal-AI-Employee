---
name: facebook-integration
description: |
  Facebook Graph API integration helper. Diagnoses token issues, lists pages,
  exchanges short-lived tokens for long-lived tokens, and tests posting.
  Use when: Facebook posting fails with AUTH_FAILED, token issues, page not found,
  setting up Facebook for the first time, troubleshooting social-mcp Facebook errors,
  or verifying the full token-to-page-to-post flow works correctly.
  Triggered by: "diagnose facebook", "fix facebook token", "facebook integration",
  "facebook auth failed", "run facebook-integration skill".
---

# Facebook Integration

Diagnose and fix Facebook Graph API integration issues step by step.

---

## When to Use What

| Symptom | Action |
|---------|--------|
| AUTH_FAILED from social-mcp | Run --diagnose first |
| data:[] from /me/accounts | No page exists yet -- see Page Creation below |
| Token expired | Run --exchange-token then --list-pages |
| Need to verify setup | Run --diagnose |
| Ready to test live post | Run --test-post |

---

## Step 1 -- Run Diagnosis

```powershell
python .claude/skills/facebook-integration/scripts/fb_setup.py --diagnose
```

This checks: token validity, permissions, expiry, and lists all pages.

---

## Step 2 -- Fix Based on Diagnosis

### Token is short-lived (expires in < 1 hour)
Exchange for long-lived token first:
```powershell
python .claude/skills/facebook-integration/scripts/fb_setup.py --exchange-token
```
Update `FACEBOOK_ACCESS_TOKEN` in `.env` and `.mcp.json` with the new token.

### No pages found (data:[])
The user must create a Facebook Page. See Page Creation Tips below.
Once created, re-run --list-pages to get the Page Access Token.

### Pages found -- extract Page Token
```powershell
python .claude/skills/facebook-integration/scripts/fb_setup.py --list-pages
```
Copy the Page Token and Page ID values. Update `.env` and `.mcp.json`:
- `FACEBOOK_ACCESS_TOKEN` = Page Token (NOT the user token)
- `FACEBOOK_PAGE_ID` = Page ID

### Missing permissions
Regenerate the token in Graph API Explorer with these scopes:
`pages_manage_posts`, `pages_read_engagement`, `pages_show_list`

---

## Step 3 -- Test Live Post

```powershell
python .claude/skills/facebook-integration/scripts/fb_setup.py --test-post
```

Success output: `SUCCESS! Post ID: ...`

---

## Page Creation Tips

If `facebook.com/pages/create` fails:
1. Try from mobile app: Menu > Pages > Create
2. Use category: Personal Blog or Entrepreneur
3. Account must have a profile photo and be a few days old
4. Wait 24-48 hours if account is new
5. Ask a friend to create the page and add you as Admin

---

## .mcp.json Token Note

Claude Code does NOT expand `${VAR}` in `.mcp.json`. Tokens must be hardcoded:
```json
"FACEBOOK_ACCESS_TOKEN": "actual_token_value_here"
```

After updating tokens, restart Claude Code for the MCP server to reload.

---

## Reference

For Graph API endpoints, error codes, and token flow details:
See `references/graph-api.md`
