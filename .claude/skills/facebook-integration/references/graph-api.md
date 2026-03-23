# Facebook Graph API Reference

## Token Types

| Type | Expires | Used For |
|------|---------|----------|
| User Access Token (short-lived) | 1-2 hours | Stepping stone only |
| User Access Token (long-lived) | 60 days | Exchange for Page token |
| Page Access Token | Never* | Posting to a Page |

*Page tokens obtained from a long-lived user token never expire unless permissions are revoked.

## Critical Distinction

- **User token** (`/me/feed`) -- personal timeline posting is DEPRECATED by Meta (2018)
- **Page token** (`/{page_id}/feed`) -- required for all API posting

## Key Endpoints

```
# Validate token
GET https://graph.facebook.com/debug_token
  ?input_token=TOKEN&access_token=APP_ID|APP_SECRET

# List pages (and get Page Access Tokens)
GET https://graph.facebook.com/v25.0/me/accounts
  ?access_token=USER_TOKEN

# Exchange for long-lived user token
GET https://graph.facebook.com/v25.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=APP_ID
  &client_secret=APP_SECRET
  &fb_exchange_token=SHORT_LIVED_TOKEN

# Post to page
POST https://graph.facebook.com/v25.0/{PAGE_ID}/feed
  ?access_token=PAGE_TOKEN
  body: {"message": "post content"}
```

## Common Error Codes

| Code | Subcode | Meaning | Fix |
|------|---------|---------|-----|
| 190 | 460 | Token expired | Regenerate token |
| 190 | 467 | Token invalid | Wrong token type or revoked |
| 200 | - | Permission missing | Re-generate token with correct scopes |
| 100 | - | Invalid parameter | Check page_id and token match |
| 368 | - | Blocked for policy | Content flagged by Meta |
| 10 | - | App not approved | Submit app for review (for production) |
| 400 | - | Bad request | Token is `${VAR}` literal (not substituted) |

## Required Permissions for Posting

- `pages_show_list` -- list pages
- `pages_manage_posts` -- create/delete posts
- `pages_read_engagement` -- read post metrics

## App Modes

| Mode | Who can use the app | Notes |
|------|-------------------|-------|
| Development | Only app admins/testers | Default; safe for testing |
| Live | All users | Requires Meta App Review for sensitive permissions |

For personal use (posting to your own page), **Development mode is sufficient**.

## Page Creation Troubleshooting

If `facebook.com/pages/create` fails:
1. Account must be at least a few days old with profile photo
2. Try from mobile app: Menu > Pages > Create
3. Use a different Facebook account (friend/family) to create the page and add you as admin
4. Try category: "Personal Blog" or "Entrepreneur" instead of business categories
5. Some new accounts have a temporary restriction -- wait 24-48 hours

## Token Flow (Correct Sequence)

```
1. Graph API Explorer -> generate short-lived User Token (with page permissions)
2. Exchange for long-lived User Token (--exchange-token)
3. Call /me/accounts to get Page Access Token (--list-pages)
4. Store Page Access Token as FACEBOOK_ACCESS_TOKEN in .env
5. Store Page ID as FACEBOOK_PAGE_ID in .env
6. Test with --test-post
```

## .env.example for Facebook

```env
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=page_access_token_here   # NOT user token
FACEBOOK_PAGE_ID=your_page_numeric_id
```
