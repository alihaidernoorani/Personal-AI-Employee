# WhatsApp Watcher Setup Guide

## Overview

The `WhatsAppWatcher` monitors WhatsApp Web for unread messages with **keyword detection**. It automatically escalates priority for messages containing:

- `urgent` → Priority: **URGENT**
- `asap` → Priority: **HIGH**
- `invoice` → Priority: **HIGH**
- `payment` → Priority: **HIGH**

Messages are saved as `WA_*.md` files in `AI_Employee_Vault/Needs_Action/` with metadata and detected keywords.

## Prerequisites

- Python 3.13+
- Playwright browser automation (Chromium)
- Active WhatsApp account with WhatsApp Web access
- Windows/macOS/Linux

## Step 1: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads a ~500MB Chromium instance (one-time setup).

## Step 2: Start the WhatsApp Watcher

```bash
cd /path/to/Personal_AI_Employee
VAULT_PATH="./AI_Employee_Vault" python orchestrator.py --watcher whatsapp
```

**First run:** A browser window will open showing WhatsApp Web with a **QR code**.

## Step 3: Scan QR Code (First Run Only)

1. **Open WhatsApp on your phone**
2. Go to **Settings → Linked devices**
3. **Point your phone camera at the QR code** in the browser
4. Click **Link This Device**
5. Wait for the page to load (usually ~10 seconds)

The session is then saved to `whatsapp_session/` (gitignored). **Subsequent runs skip the QR code.**

## Step 4: Test the Watcher

1. **Send a WhatsApp message** to yourself or a group you monitor, e.g.:
   ```
   "Urgent: Invoice due by Friday"
   ```

2. **Within 30 seconds**, a file like `WA_20260320T130000Z_john-smith.md` will appear in `AI_Employee_Vault/Needs_Action/`

3. **Check the priority:**
   ```yaml
   priority: urgent
   keywords_matched: ['urgent', 'invoice']
   ```

## Configuration

### Check Interval

Default: **30 seconds**

To change, modify in `orchestrator.py` or instantiate with:

```python
watcher = WhatsAppWatcher(vault_path="./AI_Employee_Vault", check_interval=15)
```

**Minimum recommended:** 15 seconds (balances responsiveness vs. resource usage)
**Resource-conscious:** 60+ seconds

### Custom Keywords

Edit `PRIORITY_KEYWORDS` dict in `watchers/whatsapp_watcher.py`:

```python
PRIORITY_KEYWORDS = {
    "urgent": "urgent",      # Message contains "urgent" → priority: urgent
    "asap": "high",          # Message contains "asap" → priority: high
    "invoice": "high",
    "payment": "high",
    "alert": "high",         # Add new keyword here
}
```

### Session Persistence

- **Path:** `whatsapp_session/` (in project root, gitignored)
- **Contains:** Browser cookies, local storage, authentication tokens
- **Lifecycle:** Persistent across runs until manually deleted
- **To re-authenticate:** Delete `whatsapp_session/` and run watcher again (triggers QR scan)

## File Output Example

**Filename:** `WA_20260320T130000Z_urgent-invoice.md`

```markdown
---
type: whatsapp
source: whatsapp_web
sender: "John Smith"
message_text: "Invoice #12345 due ASAP - this is urgent!"
message_hash: "a1b2c3d4e5f6g7h8"
priority: urgent
keywords_matched: ['urgent', 'asap', 'invoice']
received: "2026-03-20T13:00:00Z"
status: pending
---

## WhatsApp Message from John Smith

**Priority:** URGENT

**Message:** Invoice #12345 due ASAP - this is urgent!

## Keywords Detected

urgent, asap, invoice

## Actions

- [ ] Read full conversation in WhatsApp
- [ ] Draft reply (requires approval)
- [ ] Mark as resolved
- [ ] Escalate
```

## Troubleshooting

### "WhatsApp Web not ready — QR scan may be needed"

This means the page didn't load in time. Usually happens on first run.

**Fix:**
1. Delete `whatsapp_session/`
2. Run watcher again
3. Manually scan QR code in browser (don't skip it)
4. Wait 10–15 seconds for page to fully load

### "Playwright not found" / "chromium not installed"

```
ModuleNotFoundError: No module named 'playwright'
```

**Fix:**
```bash
pip install playwright
playwright install chromium
```

### Session keeps asking for QR code

The session file was corrupted or the browser instance failed to save it.

**Fix:**
```bash
rm -rf whatsapp_session/
# Run watcher again and rescan QR
```

### No messages appearing

1. **Verify WhatsApp Web accessibility:**
   - Open `https://web.whatsapp.com` manually
   - Ensure you can see chats and unread badges

2. **Check logs:**
   ```bash
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep whatsapp
   ```

3. **Test message:**
   - Send yourself a message
   - Ensure it shows as UNREAD (unread badge visible)
   - Wait 30 seconds
   - Check `Needs_Action/`

4. **Verify keyword detection:**
   - Send a message like "urgent payment due"
   - Should create file with `priority: urgent`
   - If not, check `PRIORITY_KEYWORDS` config

### Browser window not opening / headless mode

The watcher runs with `headless=False` (window visible) because:
- First run needs manual QR scan
- Debugging is easier with visual feedback

To run headless on subsequent runs (not recommended):
```python
headless=True,  # Only after first successful QR scan
```

### Memory/CPU usage high

WhatsApp Web can be resource-intensive. Optimization tips:

1. **Increase check interval** (30s → 60s)
2. **Reduce message retention:** Delete old `WA_*.md` files
3. **Run on separate machine:** Use `process_supervisor.py` to manage lifecycle

## Performance Notes

- **Startup:** 3–5 seconds (browser launch)
- **Snapshot extraction:** 1–2 seconds (accessibility tree parse)
- **Message processing:** <1 second per message
- **Total cycle:** ~5–10 seconds per poll (then sleeps for rest of interval)

With 30s interval: ~2–4 polls per minute, 120–240 per hour (minimal resource impact)

## Security Notes

- **Session data:** Stored in `whatsapp_session/` (local cookies, tokens)
- **No message text logged:** Only metadata (sender, priority, keywords)
- **No credentials stored:** Uses WhatsApp's OAuth (browser-based)
- **Gitignored:** `whatsapp_session/` is in `.gitignore`

## Integration with AI Employee Vault

1. Creates task files in `Needs_Action/`
2. Logs all actions to `Logs/YYYY-MM-DD.json`
3. Tracks processed message IDs in `scripts/processed_whatsapp.json` (prevents duplicates)
4. Escalates priority based on keywords
5. On error, creates `ERROR_*.md` files for manual review

## Running as Background Service

For persistent operation, use the process supervisor:

```bash
VAULT_PATH="./AI_Employee_Vault" python process_supervisor.py --watcher whatsapp
```

This keeps the watcher running and automatically restarts if it crashes.

## Tips & Tricks

### Monitor Specific Groups

Modify message extraction to filter chats:

```python
# In _extract_unread_messages(), add:
if "Finance Team" in sender or "Urgent" in sender:
    messages.append({...})
```

### Custom Alerts

Add to `_detect_priority()` for specialized rules:

```python
if "invoice" in text_lower and "10000" in text:
    return "urgent"  # High-value invoices are urgent
```

### Export Priority Messages

Create a separate folder for urgent messages:

```bash
find AI_Employee_Vault/Needs_Action -name "WA_*" -exec grep -l "priority: urgent" {} \; | xargs -I {} mv {} AI_Employee_Vault/Urgent_Messages/
```

## References

- [Playwright Documentation](https://playwright.dev/)
- [WhatsApp Web Documentation](https://www.whatsapp.com/contact/)
- [Accessibility Snapshots](https://playwright.dev/python/docs/api/class-accessibility)
