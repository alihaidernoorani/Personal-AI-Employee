# Gmail API Watcher Setup Guide

## Overview

The `GmailApiWatcher` monitors your Gmail inbox for **UNSEEN IMPORTANT** emails and creates task files in `AI_Employee_Vault/Needs_Action/`. It uses OAuth 2.0 authentication with Google's official Gmail API.

## Prerequisites

- Python 3.13+
- Google account with Gmail enabled
- Google Cloud Project with Gmail API enabled

## Step 1: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Gmail API"
   - Click **Enable**

4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Desktop application**
   - Download the JSON file (this is your `credentials.json`)

5. Place `credentials.json` in the project root:
   ```powershell
   Copy-Item "$env:USERPROFILE\Downloads\client_secret_*.json" .\credentials.json
   ```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies added:
- `google-auth-oauthlib>=1.2.0`
- `google-auth-httplib2>=0.2.0`
- `google-api-python-client>=2.100.0`

## Step 3: Run the Watcher

**Windows (recommended):** Double-click `run_gmail_api.bat` or run from PowerShell:

```powershell
.\run_gmail_api.bat
```

**PowerShell directly:**

```powershell
$env:VAULT_PATH = "$PWD\AI_Employee_Vault"
python orchestrator.py --watcher gmail_api
```

**First run:** A browser window will open asking you to authorize Gmail access. Click **Allow**. The access token will be saved to `.gmail_token.json` (gitignored).

## Step 4: Test

1. Send a test email to your inbox
2. In Gmail, mark the email as **Important** (star it or apply the IMPORTANT label)
3. Within 2 minutes (default `check_interval=120`), a file like `GMAIL_20260320T120000Z_test-email.md` should appear in `AI_Employee_Vault/Needs_Action/`
4. Verify the file contains:
   ```yaml
   ---
   type: email
   source: gmail_api
   msg_id: "..."
   sender: "..."
   subject: "..."
   snippet: "..."
   priority: high
   ```

## Configuration

### Check Interval

Modify in `watchers/gmail_api_watcher.py` or pass to constructor:

```python
watcher = GmailApiWatcher(vault_path="./AI_Employee_Vault", check_interval=120)
```

- Default: `120` seconds (2 minutes)
- Minimum recommended: `60` seconds
- For production: consider `300` (5 minutes) to respect API quotas

### Query Filter

Edit `check_for_updates()` in `watchers/gmail_api_watcher.py`:

```python
query = 'is:unread label:IMPORTANT'
```

Supported filters:
- `is:unread` — Unread messages
- `label:IMPORTANT` — Marked important
- `from:user@example.com` — From specific sender
- `subject:keyword` — Subject contains text
- `has:attachment` — Has attachments

### API Quotas

Gmail API has quotas:
- **100M requests/day** per project (shared quota)
- **1M requests/day** per user per project
- Polling every 2 minutes = ~720 requests/day (safe)

## Troubleshooting

### `credentials.json` not found

```
Error: credentials.json not found at /path/to/credentials.json
```

**Fix:** Download OAuth credentials from Google Cloud Console and place in project root.

### Token refresh failed

```
Error: Failed to refresh token
```

**Fix:** Delete `.gmail_token.json` and re-authenticate:
```powershell
Remove-Item .gmail_token.json
python orchestrator.py --watcher gmail_api
```

### "Invalid client" error

This usually means your `credentials.json` is malformed or from the wrong type (Service Account vs OAuth).

**Fix:**
1. Verify you downloaded **OAuth Client ID** (Desktop app), not Service Account credentials
2. Delete `credentials.json` and re-download from Google Cloud Console

### No emails appearing

1. Verify emails are marked **IMPORTANT** in Gmail (add star or apply label)
2. Verify they are **UNREAD**
3. Check logs:
   ```powershell
   Get-Content "AI_Employee_Vault\Logs\$(Get-Date -Format 'yyyy-MM-dd').json" -Tail 20
   ```

4. Manually test API:
   ```python
   from watchers.gmail_api_watcher import GmailApiWatcher
   watcher = GmailApiWatcher("./AI_Employee_Vault")
   watcher._authenticate()
   messages = watcher.check_for_updates()
   print(f"Found {len(messages)} unread important emails")
   ```

## File Output Example

**Filename:** `GMAIL_20260320T120000Z_urgent-invoice.md`

```markdown
---
type: email
source: gmail_api
msg_id: "18c0e7f6e1234567"
sender: "billing@acme.com"
subject: "Invoice #12345 Due"
snippet: "Your invoice is due. Please remit payment by 2026-03-25."
priority: high
received: "2026-03-20T12:00:00Z"
status: pending
---

## Email from billing@acme.com

**Subject:** Invoice #12345 Due

**Snippet:** Your invoice is due. Please remit payment by 2026-03-25.

## Actions

- [ ] Read full email in Gmail
- [ ] Draft reply
- [ ] Archive
- [ ] Add to task list
```

## Security Notes

- **Credentials:** `credentials.json` should be `.gitignore`'d (it is by default)
- **Tokens:** `.gmail_token.json` is automatically gitignored
- **Permissions:** The watcher requests `https://www.googleapis.com/auth/gmail.readonly` (read-only)
- **Rotation:** Regenerate OAuth credentials every 90 days if security is critical

## Integration with AI Employee Vault

The watcher integrates with the broader vault system:

1. Creates task files in `Needs_Action/`
2. Logs all actions to `Logs/YYYY-MM-DD.json`
3. Tracks processed message IDs in `scripts/processed_gmail_api.json` (prevents duplicates)
4. On error, creates `ERROR_*.md` files for manual review

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api/guides)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Query Syntax](https://support.google.com/mail/answer/7190)
