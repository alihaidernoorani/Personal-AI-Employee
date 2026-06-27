---
name: twitter-post
description: |
  Generates a Twitter/X post (≤280 characters, or a thread of ≤280-char tweets)
  from Business_Goals.md and Company_Handbook.md. Writes a Plan file and an
  Approval file to Pending_Approval/ for human review before publishing.
  Does NOT call any MCP tools — the boundary is writing the approval file.
  Hard constraint: each tweet must be ≤280 characters including hashtags.
  Use this skill on-demand or on a weekly schedule for Twitter/X content.
  Triggered by: "run twitter-post skill", "post to twitter", "create tweet", "post to X".
---

# Twitter/X Post

Generate a tweet or thread and route through the approval pipeline.

---

## Step 1 — Read Business Context

Read both source files:

1. `AI_Employee_Vault/Business_Goals.md` — services offered, OKRs, post topics
2. `AI_Employee_Vault/Company_Handbook.md` — brand voice, communication standards, tone

---

## Step 2 — Select a Post Topic

Choose the most relevant topic from `## LinkedIn Post Topics` in `Business_Goals.md` based on:
- Which topics have NOT been posted to Twitter recently (check `Plans/` for recent Twitter plans)
- Current day/month context
- Default to the first unused topic if no strong signal

---

## Step 3 — Generate the Tweet(s)

### Hard constraint: every tweet ≤ 280 characters (count carefully, including spaces and hashtags)

**Single tweet** (preferred): 1 tweet with the key message and 1–2 hashtags.

**Thread** (use only when the topic genuinely requires more depth): up to 5 tweets numbered
1/N, 2/N, etc. Each tweet ≤ 280 characters independently.

### Tweet structure (single tweet):
1. Hook or key insight (direct, punchy — Twitter rewards brevity)
2. Value statement or service mention (compressed)
3. CTA (DM, reply, or "Link in bio")
4. 1–2 hashtags (leave space for the hashtags in the 280-char budget)

### Thread structure (if needed):
- Tweet 1: Hook + thesis
- Tweets 2–4: One supporting point each
- Tweet N (last): CTA + 1–2 hashtags

### Character counting rule:
After drafting each tweet, count characters. If any tweet exceeds 280, rewrite it.
URLs count as 23 characters regardless of actual length (Twitter's t.co wrapping).

---

## Step 4 — Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_twitter.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSZ`.

```markdown
---
type: plan
source_task: twitter_post_request
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
topic: "<selected topic title>"
is_thread: false
tweet_count: 1
---

## Summary

Twitter/X post generated from Business_Goals.md topic: <topic title>.

## Tweet Content

<!-- For a single tweet: -->
**Tweet (N chars):**
<tweet text>

<!-- For a thread: -->
**Tweet 1/N (N chars):**
<tweet 1 text>

**Tweet 2/N (N chars):**
<tweet 2 text>

## Notes

Is thread: <true/false>
Tweet count: <number>
Hashtags used: <hashtags>
Service referenced: <service name>
CTA type: <DM / reply / link in bio>
```

---

## Step 5 — Write Approval File

Create `AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_twitter.md`
using the same `<timestamp>` as the Plan file.

```markdown
---
type: approval_request
action: twitter_post
plan_file: "PLAN_<timestamp>_twitter.md"
reason: "Twitter/X lead-generation post per Business_Goals.md schedule"
parameters:
  content: |
    <Full tweet text — for threads, all tweets separated by "---">
  is_thread: false
  tweet_count: 1
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

Publishing to Twitter/X is an external, irreversible action. Human review
ensures the content is accurate, on-brand, and within character limits.

## Action Summary

**Platform**: Twitter/X
**Is thread**: <true/false>
**Tweet count**: <number>
**Topic**: <topic title>
**Action**: Move this file to `Approved/` to publish, or `Rejected/` to discard.
```

---

## Step 6 — Execute (after approval)

When `APPROVAL_<timestamp>_twitter.md` is moved to `AI_Employee_Vault/Approved/`,
the `execute-plan` skill calls:

For a single tweet:
```
mcp__social-mcp__post_twitter
  content: <content from approval file parameters.content>
  approval_id: <approval filename stem>
```

For a thread, post each tweet sequentially, passing `reply_to_tweet_id` for tweets 2+.

**Required `.env` keys:**

| Key | Description |
|-----|-------------|
| `TWITTER_BEARER_TOKEN` | App-only Bearer Token from Twitter Developer Portal |
| `TWITTER_API_KEY` | OAuth 1.0a API Key (for user-context posting) |
| `TWITTER_API_SECRET` | OAuth 1.0a API Secret |
| `TWITTER_ACCESS_TOKEN` | User Access Token |
| `TWITTER_ACCESS_TOKEN_SECRET` | User Access Token Secret |

**Note:** Posting requires OAuth 1.0a user context (not just Bearer Token).
The social-mcp server handles token signing automatically when all 5 keys are set.

---

## Step 7 — Log the Action

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "twitter_post_drafted",
  "actor": "claude_code",
  "target": "Twitter/X",
  "parameters": {
    "plan_file": "<PLAN_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename>",
    "is_thread": false,
    "tweet_count": 1
  },
  "approval_status": "deferred",
  "approved_by": "pending",
  "result": "deferred"
}
```

---

## Completion Signal

When the Plan file, Approval file, and log entry are all written, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
