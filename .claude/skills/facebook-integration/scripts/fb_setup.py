"""
Facebook Graph API setup utility.

Commands:
  python fb_setup.py --check-token       Validate token and show permissions/expiry
  python fb_setup.py --list-pages        List all pages managed by this user
  python fb_setup.py --exchange-token    Exchange short-lived token for long-lived (60-day)
  python fb_setup.py --test-post         Post a test message to the configured page
  python fb_setup.py --diagnose          Run all checks and show full diagnosis

Reads from .env: FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# Load .env from project root (3 levels up from this script)
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
APP_ID = os.getenv("FACEBOOK_APP_ID", "")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
BASE = "https://graph.facebook.com/v25.0"


def check_token():
    if not TOKEN:
        print("ERROR: FACEBOOK_ACCESS_TOKEN not set in .env")
        return False
    resp = requests.get(
        "https://graph.facebook.com/debug_token",
        params={"input_token": TOKEN, "access_token": f"{APP_ID}|{APP_SECRET}"},
        timeout=15,
    )
    data = resp.json().get("data", {})
    print(json.dumps(data, indent=2))
    if not data.get("is_valid"):
        print("\nToken is INVALID or expired.")
        return False
    print(f"\nToken is VALID. Type: {data.get('type')} | App: {data.get('app_id')}")
    scopes = data.get("scopes", [])
    print(f"Scopes: {', '.join(scopes)}")
    required = {"pages_manage_posts", "pages_show_list"}
    missing = required - set(scopes)
    if missing:
        print(f"WARNING: Missing required scopes: {missing}")
    expires = data.get("expires_at", 0)
    if expires:
        import datetime
        exp = datetime.datetime.fromtimestamp(expires)
        print(f"Expires: {exp}")
    return True


def list_pages():
    if not TOKEN:
        print("ERROR: FACEBOOK_ACCESS_TOKEN not set in .env")
        return
    resp = requests.get(f"{BASE}/me/accounts", params={"access_token": TOKEN}, timeout=15)
    data = resp.json()
    if "error" in data:
        print(f"ERROR: {data['error']['message']}")
        print("\nCommon causes:")
        print("  - Token is a short-lived token (exchange it first with --exchange-token)")
        print("  - Token missing pages_show_list permission")
        print("  - No Facebook Pages exist for this account")
        return
    pages = data.get("data", [])
    if not pages:
        print("No pages found. You must create a Facebook Page first.")
        print("Go to: https://www.facebook.com/pages/create")
        return
    print(f"Found {len(pages)} page(s):\n")
    for p in pages:
        print(f"  Name:         {p['name']}")
        print(f"  Page ID:      {p['id']}")
        print(f"  Page Token:   {p['access_token'][:40]}...")
        print(f"  Permissions:  {', '.join(p.get('tasks', []))}")
        print()
    print("Copy the Page Token and Page ID into your .env as:")
    print("  FACEBOOK_ACCESS_TOKEN=<page_token>")
    print("  FACEBOOK_PAGE_ID=<page_id>")


def exchange_token():
    if not all([TOKEN, APP_ID, APP_SECRET]):
        print("ERROR: FACEBOOK_ACCESS_TOKEN, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET must all be set")
        return
    resp = requests.get(
        f"{BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": TOKEN,
        },
        timeout=15,
    )
    data = resp.json()
    if "error" in data:
        print(f"ERROR: {data['error']['message']}")
        return
    long_lived = data.get("access_token")
    print(f"Long-lived token obtained.")
    print(f"\nUpdate your .env:\n  FACEBOOK_ACCESS_TOKEN={long_lived}")
    print("\nThen run --list-pages to get your Page Access Token.")


def test_post():
    if not TOKEN or not PAGE_ID:
        print("ERROR: FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID must be set in .env")
        return
    message = "This is a test post from the Personal AI Employee system. Ignore."
    resp = requests.post(
        f"{BASE}/{PAGE_ID}/feed",
        params={"access_token": TOKEN},
        json={"message": message},
        timeout=15,
    )
    data = resp.json()
    if "error" in data:
        print(f"ERROR {resp.status_code}: {data['error']['message']}")
        print(f"Code: {data['error'].get('code')} | Subcode: {data['error'].get('error_subcode')}")
        print("\nSee references/graph-api.md for error code explanations.")
        return
    print(f"SUCCESS! Post ID: {data.get('id')}")
    print(f"URL: https://www.facebook.com/{data.get('id')}")


def diagnose():
    print("=" * 50)
    print("Facebook Integration Diagnosis")
    print("=" * 50)
    print(f"\n.env path: {env_path}")
    print(f"FACEBOOK_APP_ID:      {'set' if APP_ID else 'MISSING'}")
    print(f"FACEBOOK_APP_SECRET:  {'set' if APP_SECRET else 'MISSING'}")
    print(f"FACEBOOK_ACCESS_TOKEN: {'set' if TOKEN else 'MISSING'}")
    print(f"FACEBOOK_PAGE_ID:     {PAGE_ID if PAGE_ID else 'MISSING'}")
    print("\n--- Token Check ---")
    valid = check_token()
    if valid:
        print("\n--- Pages ---")
        list_pages()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Graph API setup utility")
    parser.add_argument("--check-token", action="store_true")
    parser.add_argument("--list-pages", action="store_true")
    parser.add_argument("--exchange-token", action="store_true")
    parser.add_argument("--test-post", action="store_true")
    parser.add_argument("--diagnose", action="store_true")
    args = parser.parse_args()

    if args.check_token:
        check_token()
    elif args.list_pages:
        list_pages()
    elif args.exchange_token:
        exchange_token()
    elif args.test_post:
        test_post()
    elif args.diagnose:
        diagnose()
    else:
        parser.print_help()
