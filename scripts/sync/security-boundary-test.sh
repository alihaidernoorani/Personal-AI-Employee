#!/usr/bin/env bash
# security-boundary-test.sh — Verify cloud VM holds zero execution credentials.
# Usage: ./security-boundary-test.sh [ssh_user@host]
# If no argument, runs locally (for cloud-side self-check).
# Outputs PASS/FAIL per check. Exits 0 if all PASS, 1 if any FAIL.
set -euo pipefail

SSH_TARGET="${1:-}"
PASS=0
FAIL=0

run_check() {
    local description="$1"
    local command="$2"
    local expect_empty="${3:-true}"  # true = expect no output (nothing found = good)

    if [ -n "$SSH_TARGET" ]; then
        output=$(ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_TARGET" "$command" 2>/dev/null || true)
    else
        output=$(eval "$command" 2>/dev/null || true)
    fi

    if [ "$expect_empty" = "true" ]; then
        if [ -z "$output" ]; then
            echo "PASS: $description"
            PASS=$((PASS + 1))
        else
            echo "FAIL: $description"
            echo "      Found: $output"
            FAIL=$((FAIL + 1))
        fi
    else
        if [ -n "$output" ]; then
            echo "PASS: $description"
            PASS=$((PASS + 1))
        else
            echo "FAIL: $description"
            FAIL=$((FAIL + 1))
        fi
    fi
}

echo "=== Security Boundary Test ==="
echo "Target: ${SSH_TARGET:-localhost}"
echo ""

# Check 1: No .env file anywhere under /root/
run_check "No .env file under /root/" \
    "find /root/ -name '.env' -not -path '/root/.local/*' 2>/dev/null | head -5"

# Check 2: No .env.* files
run_check "No .env.* files under /root/ (excluding .env.cloud)" \
    "find /root/ -name '.env.*' -not -name '.env.cloud' -not -path '/root/.local/*' 2>/dev/null | head -5"

# Check 3: No *.token files
run_check "No *.token credential files under /root/" \
    "find /root/ -name '*.token' -o -name '*_token.json' 2>/dev/null | grep -v '.gmail_mcp_token' | head -5"

# Check 4: No credential JSON files
run_check "No credentials.json under /root/" \
    "find /root/ -name 'credentials.json' 2>/dev/null | head -5"

# Check 5: No .mcp.json at project root
run_check "No .mcp.json present" \
    "find /root/ -maxdepth 3 -name '.mcp.json' 2>/dev/null | head -5"

# Check 6: No email/social MCP processes running
run_check "No email/social MCP processes running" \
    "ps aux 2>/dev/null | grep -E 'email-mcp|social-mcp|browser-mcp' | grep -v grep"

# Check 7: No browser session directories
run_check "No browser session directories" \
    "find /root/ -type d -name 'session' -o -name 'cookies' 2>/dev/null | head -5"

# Check 8: ODOO_DRAFT_ONLY is set
run_check "ODOO_DRAFT_ONLY env var configured" \
    "grep -r 'ODOO_DRAFT_ONLY=true' /root/.env.cloud /root/.env 2>/dev/null | head -1" \
    "false"

echo ""
echo "=== Results: ${PASS} PASS, ${FAIL} FAIL ==="

if [ "$FAIL" -gt 0 ]; then
    echo "SECURITY BOUNDARY: FAIL"
    exit 1
else
    echo "SECURITY BOUNDARY: PASS"
    exit 0
fi
