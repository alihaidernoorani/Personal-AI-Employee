# Credential Setup Guide — Social Media & Odoo MCP

> **Purpose:** Step-by-step instructions to configure the three unconfigured integrations:
> Facebook (refresh expired token), Instagram, Twitter/X, and Odoo (live mode).
>
> All tokens go in `.mcp.json` at the project root (already gitignored).
> Never put them in `.env.example`, `CLAUDE.md`, or any tracked file.

---

## Table of Contents

1. [Facebook — Full Setup from Scratch](#1-facebook--full-setup-from-scratch)
2. [Instagram — First-Time Setup](#2-instagram--first-time-setup)
3. [Twitter / X — Bearer Token + Posting Credentials](#3-twitter--x--bearer-token--posting-credentials)
4. [Odoo Community — Local Docker Setup](#4-odoo-community--local-docker-setup)
5. [Updating `.mcp.json` After Each Step](#5-updating-mcp-json-after-each-step)

---

## 1. Facebook — Full Setup from Scratch

This section covers the entire process from zero: creating a Meta Developer account,
building the app, setting permissions, and generating a **never-expiring Page Access Token**
that lets the AI Employee post to your Facebook Page.

> **Why your previous token failed:** Short-lived User Tokens expire in ~1 hour. If you
> used one directly in `.mcp.json`, it stopped working immediately. This guide generates
> a proper **Page Access Token** (no expiry) via a two-step exchange.

---

### Part A — Create Your Meta Developer Account

> Skip to Part B if you already have a Meta Developer account.

**A1.** Go to [https://developers.facebook.com](https://developers.facebook.com) and click
**"Get Started"** in the top right.

**A2.** Log in with your personal Facebook account (the one that is Admin of your Page).

**A3.** Accept the Meta Platform Policies when prompted.

**A4.** You are now a registered developer. You will land on the **My Apps** page at
[https://developers.facebook.com/apps/](https://developers.facebook.com/apps/).

---

### Part B — Create the Meta App

**B1.** On the **My Apps** page, click **"Create App"** (top right).

**B2.** The creation wizard has four screens:

| Screen | What to do |
|--------|------------|
| **App details** | Enter any app name (e.g. `AI Employee`) and your contact email. Click **Next**. |
| **Use cases** | Click **"Other"** at the bottom of the list (we need manual permission control). Click **Next**. |
| **App type** | Select **"Business"**. Click **Next**. |
| **Business portfolio** | Select **"I don't want to connect a business portfolio yet"** (you can link one later). Click **Next**. |

**B3.** Review the summary and click **"Go to dashboard"**. Your app is created.

**B4.** You are now in the **App Dashboard**. Note your **App ID** shown at the top — you
will need it shortly. To find your **App Secret**: click **App Settings → Basic** in the
left sidebar, then click **"Show"** next to App Secret.

> Save App ID and App Secret now — you will need both in Part D.

---

### Part C — Add the Facebook Login for Business Product

**C1.** In the left sidebar of your App Dashboard, click **"Add Product"** (near the bottom).

**C2.** Find **"Facebook Login for Business"** and click **"Set Up"**.

**C3.** In the left sidebar you will now see **"Facebook Login for Business"** → click it,
then click **"Settings"**.

**C4.** Under **"Valid OAuth Redirect URIs"** add `https://localhost` (required even though
we won't use it for this flow). Click **"Save Changes"**.

---

### Part D — Configure Permissions in Graph API Explorer

The Graph API Explorer is Meta's built-in tool for generating tokens and testing API calls.
You will use it to get a short-lived User Token, which you then exchange for a long-lived
Page Access Token.

**D1.** Open the Graph API Explorer:
[https://developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)

**D2.** In the **"Meta App"** dropdown (top right of the Explorer), select the app you
just created (`AI Employee`).

**D3.** Confirm the **"User or Page"** dropdown shows **"User Token"** (not Page Token).

**D4.** Click **"Add a Permission"** and add each of the following one at a time:

| Permission | Purpose |
|------------|---------|
| `pages_show_list` | List all Pages you manage |
| `pages_manage_posts` | Create and publish posts |
| `pages_manage_metadata` | Read Page metadata |
| `pages_read_engagement` | Read likes, comments, shares |

**D5.** Click **"Generate Access Token"**.

**D6.** A Facebook popup appears. Click **"Continue as [Your Name]"**, then select
**your Facebook Page** from the list, then click **"Continue"**, then **"Done"**.

**D7.** The Access Token field in the Explorer now shows a long string — copy it.
This is your **short-lived User Token** (expires in ~1 hour).

---

### Part E — Exchange for a Long-Lived User Token (60 days)

You cannot use the short-lived token directly. Exchange it via this API call.

**E1.** Paste this URL into your browser, replacing the three placeholders:

```
https://graph.facebook.com/v20.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_USER_TOKEN
```

- `YOUR_APP_ID` — from App Settings > Basic
- `YOUR_APP_SECRET` — from App Settings > Basic (click Show first)
- `SHORT_LIVED_USER_TOKEN` — the token you copied in Step D7

**E2.** The browser returns a JSON response like:

```json
{
  "access_token": "EAAxxxxxxxxxxxxxxxxxx...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

Copy the `access_token` value — this is your **60-day Long-Lived User Token**.

---

### Part F — Get the Never-Expiring Page Access Token

A Page Access Token generated from a Long-Lived User Token does not expire on its own.
It only invalidates if you change your Facebook password or revoke the app.

**F1.** Paste this URL into your browser (replace `YOUR_60_DAY_USER_TOKEN`):

```
https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_60_DAY_USER_TOKEN
```

**F2.** The response is a JSON array of Pages you manage. Find your page by name. It looks like:

```json
{
  "data": [
    {
      "access_token": "EAAxxxxxxxxxxxxxxxxxx...",
      "category": "Software",
      "name": "Your Page Name",
      "id": "122095165736908825",
      "tasks": ["ANALYZE", "ADVERTISE", "MODERATE", "CREATE_CONTENT"]
    }
  ]
}
```

**F3.** Copy the `access_token` from your page's entry — this is your **Page Access Token**.

> **Important:** Copy the `access_token` from inside `data[0]`, not the URL parameter
> you just used. They are different tokens.

---

### Part G — Verify the Token

**G1.** Go to the Access Token Debugger:
[https://developers.facebook.com/tools/debug/accesstoken/](https://developers.facebook.com/tools/debug/accesstoken/)

**G2.** Paste your Page Access Token into the field and click **"Debug"**.

**G3.** Confirm all three of these:

| Field | Expected value |
|-------|----------------|
| **Type** | `Page` |
| **Expires** | `Never` |
| **Scopes** | Includes `pages_manage_posts` and `pages_show_list` |

If **Expires** shows a date instead of "Never", you copied the wrong token (you may
have copied the User Token instead of the Page Token). Go back to Part F.

---

### Part H — Update `.mcp.json`

Open `.mcp.json` in the project root and replace the `FACEBOOK_ACCESS_TOKEN` value
in the `social-mcp` block:

```json
"FACEBOOK_ACCESS_TOKEN": "PASTE_YOUR_PAGE_ACCESS_TOKEN_HERE"
```

Your Page ID (`122095165736908825`) is already in `.mcp.json` — no change needed there.

---

### Part I — Test the Integration

**I1.** Restart Claude Code to reload the MCP server (close and reopen, or run `/mcp`).

**I2.** Confirm `DRY_RUN` is `"false"` in the `social-mcp` block of `.mcp.json`.

**I3.** In Claude, run:
```
Use the post_facebook tool with content "Test post from AI Employee" and approval_id "test-001"
```

A successful response returns a `post_id`. You can verify the post appeared on your
Page (you may want to delete it afterwards).

---

### Token Maintenance

| Scenario | Action |
|----------|--------|
| Token suddenly stops working | You changed your Facebook password — repeat Parts D → H |
| App permissions were revoked | Repeat Parts D → H |
| You want to post from a different page | Repeat Part F with the same User Token, copy a different entry from the array |

---

## 2. Instagram — First-Time Setup

> **Important (2026):** The Instagram Basic Display API was **deprecated on December 4, 2024**
> and no longer works. You must use the **Instagram Graph API**, which requires:
> - An **Instagram Business** or **Creator** account
> - Your Instagram account **linked to a Facebook Page**
> - The same Meta Developer App used for Facebook

> **Also important:** The Instagram Graph API only supports **media posts** (photos/videos).
> Text-only posts are not supported. Your post must include an image URL.

### Prerequisites

1. Go to your Instagram profile → **Settings** → **Account type and tools** → **Switch to Professional Account** → choose **Business**
2. During setup, link it to your Facebook Page when prompted

### Step 1 — Add Instagram Product to Your Meta App

1. Go to [https://developers.facebook.com/apps/](https://developers.facebook.com/apps/) and open your app
2. In the left sidebar, click **"Add Product"**
3. Find **"Instagram Graph API"** and click **"Set Up"**

### Step 2 — Get a User Token with Instagram Permissions

1. Go to [https://developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Select your app from the **"Meta App"** dropdown
3. Add these permissions:
   - `pages_show_list`
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. Click **"Generate Access Token"** and authorize — make sure to select both your Facebook Page **and** your Instagram account

### Step 3 — Get Your Instagram Business Account ID

After generating the token, run this in Graph API Explorer (GET request):

```
/me/accounts
```

Find your page in the response, copy its `id`. Then call:

```
/{PAGE_ID}?fields=instagram_business_account
```

Copy the `id` from `instagram_business_account` — this is your **Instagram User ID**.

### Step 4 — Exchange for Long-Lived Token

Same process as Facebook Step 3:

```
https://graph.facebook.com/v20.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=YOUR_APP_ID
  &client_secret=YOUR_APP_SECRET
  &fb_exchange_token=SHORT_LIVED_TOKEN
```

Copy the resulting long-lived token.

### Step 5 — Update `.mcp.json`

In the `social-mcp` block:

```json
"INSTAGRAM_ACCESS_TOKEN": "PASTE_YOUR_LONG_LIVED_TOKEN_HERE",
"INSTAGRAM_USER_ID": "PASTE_YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID_HERE"
```

### Step 6 — Test a Post (Dry Run First)

Confirm `DRY_RUN` is `"true"` in `social-mcp` env, then from Claude:

```
Use post_instagram with caption "Test post" and image_url "https://example.com/image.jpg" and approval_id "test"
```

It should return `{"dry_run": true, ...}`.

---

## 3. Twitter / X — Bearer Token + Posting Credentials

> **Pricing note (2026):** X API now uses **consumption-based billing** with no fixed monthly
> caps. The free tier has limited rate limits sufficient for the AI Employee's weekly posting.
> Check [https://docs.x.com/x-api/getting-started/getting-access](https://docs.x.com/x-api/getting-started/getting-access) for current tier details.

> **Note:** `social-mcp/server.py` already uses **OAuth 1.0a** (API Key + Secret + Access Token + Secret)
> for posting. Just set the five env vars in `.env` — no code changes needed.

### Step 1 — Create a Developer Account

1. Go to [https://console.x.com](https://console.x.com)
2. Sign in with your X (Twitter) account
3. Review and accept the **Developer Agreement and Policy**
4. Fill in the use-case description (e.g., "Automated business social media posting for personal AI employee project")

### Step 2 — Create an App

1. From the Developer Console dashboard, click **"+ Create App"**
2. Provide a name (e.g., `ai-employee-poster`), description, and use case

### Step 3 — Set App Permissions to Read + Write

1. In your App settings, go to **"User authentication settings"**
2. Click **"Set up"**
3. Set **App permissions** to **"Read and Write"**
4. Set **Type of App** to **"Web App, Automated App or Bot"**
5. Fill in a Callback URL (use `https://localhost` if you don't have one) and Website URL
6. Click **Save**

> **Important:** You must set permissions **before** generating tokens. If you generate
> tokens first and then change permissions, you must regenerate the tokens.

### Step 4 — Get Your Keys and Tokens

1. Go to your App → **"Keys and tokens"** tab
2. Under **"Consumer Keys"**, click **"Regenerate"** and copy:
   - `API Key` (also called Consumer Key)
   - `API Key Secret` (also called Consumer Secret)
3. Under **"Authentication Tokens"**, click **"Generate"** and copy:
   - `Access Token`
   - `Access Token Secret`
4. Also copy the **Bearer Token** from the same page

> Save all five values in a secure location immediately — they are only shown once.

### Step 5 — Add Credentials to `.env`

Add the following to your `.env` file:

```env
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_key_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

> `social-mcp/server.py` and `requirements.txt` already have OAuth 1.0a support built in — no code changes needed.

---

## 4. Odoo Community — Local Docker Setup

> **Current state:** The `odoo-mcp` is set to `DRY_RUN=true` in `.mcp.json` (safe demo mode).
> It works correctly in dry-run — all tools return mock data.
> Follow these steps only if you want **live Odoo integration**.

### Prerequisites

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) installed and running

### Step 1 — Create Project Folder

```powershell
mkdir C:\odoo-docker
mkdir C:\odoo-docker\config
mkdir C:\odoo-docker\addons
```

### Step 2 — Create `docker-compose.yml`

Create `C:\odoo-docker\docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - odoo-db-data:/var/lib/postgresql/data

  odoo:
    image: odoo:17.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
    environment:
      HOST: db
      USER: odoo
      PASSWORD: odoo

volumes:
  odoo-web-data:
  odoo-db-data:
```

### Step 3 — Create `odoo.conf`

Create `C:\odoo-docker\config\odoo.conf`:

```ini
[options]
addons_path = /mnt/extra-addons
data_dir = /var/lib/odoo
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
```

### Step 4 — Start Odoo

```powershell
cd C:\odoo-docker
docker compose up -d
```

First run downloads ~2 GB of images. Wait ~60 seconds, then open:

```
http://localhost:8069
```

### Step 5 — Create the Database

1. You'll see the Odoo database creation screen
2. Fill in:
   - **Master Password:** set a secure password (save it)
   - **Database Name:** `odoo`
   - **Email:** `admin@example.com`
   - **Password:** `admin` (change after first login)
3. Check **"Demo data"** if you want sample data
4. Click **"Create database"** — takes ~2 minutes

### Step 6 — Enable the Accounting Module

1. Log in as admin
2. Go to **Apps** → search for `Accounting`
3. Click **Install**

### Step 7 — Get the Admin API Password

The MCP server authenticates via `/web/session/authenticate`. Your credentials are:
- **URL:** `http://localhost:8069`
- **Database:** `odoo`
- **Username:** `admin`
- **Password:** whatever you set in Step 5

### Step 8 — Set Up HTTPS for the MCP Server

The `odoo-mcp` server **requires HTTPS** (`ODOO_URL` must start with `https://`).
For local development, use a simple nginx reverse proxy with a self-signed cert:

**Option A (Recommended for demo):** Keep `DRY_RUN=true` in `.mcp.json` — the MCP
returns realistic mock data without needing a real Odoo instance.

**Option B (Live mode):** Install [mkcert](https://github.com/FiloSottile/mkcert) to
create a trusted localhost certificate, then configure nginx to proxy
`https://localhost:8443` → `http://localhost:8069`. Update `.mcp.json`:

```json
"ODOO_URL": "https://localhost:8443",
"ODOO_DB": "odoo",
"ODOO_USERNAME": "admin",
"ODOO_PASSWORD": "your-admin-password",
"DRY_RUN": "false"
```

---

## 5. Updating `.mcp.json` After Each Step

Open `.mcp.json` in the project root. The `social-mcp` block should end up looking like:

```json
"social-mcp": {
  "command": "C:\\Program Files\\Python313\\python.exe",
  "args": ["C:\\Users\\DELL\\Documents\\GitHub\\Personal_AI_Employee\\mcp-servers\\social-mcp\\server.py"],
  "env": {
    "VAULT_PATH": "C:\\Users\\DELL\\Documents\\GitHub\\Personal_AI_Employee\\AI_Employee_Vault",
    "LINKEDIN_ACCESS_TOKEN": "YOUR_EXISTING_LINKEDIN_TOKEN",
    "FACEBOOK_ACCESS_TOKEN": "NEVER_EXPIRING_PAGE_ACCESS_TOKEN",
    "FACEBOOK_PAGE_ID": "122095165736908825",
    "INSTAGRAM_ACCESS_TOKEN": "LONG_LIVED_INSTAGRAM_TOKEN",
    "INSTAGRAM_USER_ID": "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID",
    "TWITTER_BEARER_TOKEN": "YOUR_BEARER_TOKEN",
    "TWITTER_API_KEY": "YOUR_API_KEY",
    "TWITTER_API_SECRET": "YOUR_API_SECRET",
    "TWITTER_ACCESS_TOKEN": "YOUR_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET": "YOUR_ACCESS_TOKEN_SECRET",
    "DRY_RUN": "false"
  }
}
```

After updating `.mcp.json`, **restart Claude Code** to reload the MCP servers:

```powershell
# Close Claude Code and reopen, or:
# In Claude Code, run /mcp to confirm servers are connected
```

---

## Quick Checklist

| Task | Done? |
|------|-------|
| Facebook never-expiring Page Token obtained | [ ] |
| Facebook token verified as `Type: Page, Expires: Never` | [ ] |
| Instagram Business account linked to Facebook Page | [ ] |
| Instagram `instagram_content_publish` permission granted | [ ] |
| Instagram User ID (Business Account ID) obtained | [ ] |
| Twitter Developer account created at developer.x.com | [ ] |
| Twitter App permissions set to Read + Write | [ ] |
| Twitter OAuth 1.0a tokens generated (all 4 values) | [ ] |
| `requests-oauthlib` added to requirements.txt | [ ] |
| social-mcp `_post_twitter` updated to use OAuth 1.0a | [ ] |
| Odoo Docker running at localhost:8069 (optional) | [ ] |
| Accounting module installed in Odoo (optional) | [ ] |
| `.mcp.json` updated with all new credentials | [ ] |
| Claude Code restarted to reload MCP servers | [ ] |

---

## Token Maintenance Schedule

| Token | Expiry | Action |
|-------|--------|--------|
| Facebook Page Access Token | Never (under normal conditions) | Refresh if you change Facebook password |
| Instagram long-lived token | 60 days | Exchange for new long-lived token before expiry |
| Twitter/X Bearer Token | Never | Regenerate only if compromised |
| Twitter OAuth 1.0a tokens | Never | Regenerate only if compromised |
| LinkedIn Access Token | ~60 days | Regenerate via LinkedIn Developer portal |

> **Instagram token renewal:** The Instagram Graph API token expires after 60 days.
> You can refresh it before expiry by calling:
> `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=CURRENT_TOKEN`

---

*Sources consulted:*
- [Meta Graph API: Long-Lived Tokens](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/)
- [Meta Pages API Getting Started](https://developers.facebook.com/docs/pages-api/getting-started/)
- [Instagram Graph API 2026 Guide](https://elfsight.com/blog/instagram-graph-api-complete-developer-guide-for-2026/)
- [Instagram Access Token Reference](https://developers.facebook.com/docs/instagram-platform/reference/access_token/)
- [X API Bearer Tokens](https://docs.x.com/fundamentals/authentication/oauth-2-0/bearer-tokens)
- [How to Get X API Key 2026](https://elfsight.com/blog/how-to-get-x-twitter-api-key-in-2026/)
- [Odoo on Windows Docker Compose](https://opensourcehustle.com/blog/odoo-erp-1/odoo-windows-docker-compose-7)
- [Odoo Official Docker Image](https://hub.docker.com/_/odoo)
