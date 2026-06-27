---
name: social-post-weekly
description: |
  Orchestrates the full weekly social media content pipeline across all four
  platforms: LinkedIn, Facebook, Instagram, and Twitter/X. Reads Business_Goals.md
  and Company_Handbook.md once, selects a unified topic, generates platform-specific
  content for each, and writes four Plan files and four Approval files to
  Pending_Approval/ in a single invocation. Does NOT call any MCP tools.
  Each platform's content is tailored to platform norms (LinkedIn: professional,
  Facebook: story-driven, Instagram: visual + caption, Twitter: ≤280 chars).
  Use this skill every Monday morning or on-demand to queue a full week of social content.
  Triggered by: "run social-post-weekly skill", "generate weekly social posts",
  "queue social media for this week", "weekly content".
---

# Social Post Weekly

Generate a full week of social media content across all four platforms
in one pass and route all posts through the approval pipeline.

---

## Step 1 — Read Business Context

Read both source files once (shared across all four platforms):

1. `AI_Employee_Vault/Business_Goals.md` — services, OKRs, post topics, targets
2. `AI_Employee_Vault/Company_Handbook.md` — brand voice, communication standards

Check `Plans/` for recent social plan files to avoid repeating topics.

---

## Step 2 — Select a Unified Topic

Pick ONE topic from `## LinkedIn Post Topics` in `Business_Goals.md` that:
- Has not been used on any platform in the last 7 days (check Plans/ filenames)
- Is contextually relevant to the current date/quarter
- Has enough substance for all four platform formats

Document the chosen topic and the rationale in the batch plan (Step 3).

---

## Step 3 — Write Batch Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_social_weekly.md`:

```markdown
---
type: plan
source_task: social_weekly_request
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
topic: "<selected topic>"
platforms: [linkedin, facebook, instagram, twitter]
---

## Summary

Weekly social batch: <topic> across LinkedIn, Facebook, Instagram, Twitter/X.

## Topic Rationale

<Why this topic was chosen: unused recently, contextually relevant, etc.>

## Platform Posts

### LinkedIn
<Full LinkedIn post content>

### Facebook
<Full Facebook post content>

### Instagram
**Caption:**
<Full Instagram caption>

**Image Prompt:**
<2–4 sentence image description for owner to source>

### Twitter/X
<Tweet text (≤280 chars)>
*Character count: N/280*

## Notes

LinkedIn word count: <N>
Facebook word count: <N>
Instagram word count: <N>
Twitter/X char count: <N>/280
```

---

## Step 4 — Generate Platform Content

Generate all four posts using the shared topic. Apply platform-specific rules:

### LinkedIn (100–300 words)
- Professional, insight-led tone
- Structure: hook → value → service mention → social proof → CTA → 3–5 hashtags
- No emojis unless permitted in Company_Handbook.md

### Facebook (100–300 words)
- Warmer, more story-driven than LinkedIn
- Structure: hook → value → service → CTA → 3–5 hashtags
- Slightly more conversational; Facebook audiences expect more personal connection

### Instagram (100–300 word caption)
- Visual-first framing — describe what the accompanying image shows in the caption
- Structure: question/hook → insight → service mention → CTA → line break → 5–10 hashtags
- Direct to "link in bio" (no clickable URLs in caption)
- Include a 2–4 sentence image prompt for the owner to source an image

### Twitter/X (≤280 characters, hard limit)
- Punchy hook, compressed value statement, CTA, 1–2 hashtags
- Count characters before finalising — rewrite if over 280
- Thread (up to 5 tweets) only if topic absolutely requires depth; default to single tweet

---

## Step 5 — Write Four Approval Files

Write one approval file per platform. Use the same `<timestamp>` for all four
(the batch timestamp) to make the batch easy to identify.

### 5a. LinkedIn Approval

`AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_linkedin.md`

```markdown
---
type: approval_request
action: linkedin_post
plan_file: "PLAN_<timestamp>_social_weekly.md"
reason: "Weekly LinkedIn post — social batch <timestamp>"
parameters:
  post_content: |
    <LinkedIn post content>
timestamp: "<ISO-8601 UTC>"
status: pending
---
**Platform**: LinkedIn | **Topic**: <topic> | **Words**: <N>
Move to `Approved/` to publish or `Rejected/` to discard.
```

### 5b. Facebook Approval

`AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_facebook.md`

```markdown
---
type: approval_request
action: facebook_post
plan_file: "PLAN_<timestamp>_social_weekly.md"
reason: "Weekly Facebook post — social batch <timestamp>"
parameters:
  post_content: |
    <Facebook post content>
timestamp: "<ISO-8601 UTC>"
status: pending
---
**Platform**: Facebook | **Topic**: <topic> | **Words**: <N>
Move to `Approved/` to publish or `Rejected/` to discard.
```

### 5c. Instagram Approval

`AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_instagram.md`

```markdown
---
type: approval_request
action: instagram_post
plan_file: "PLAN_<timestamp>_social_weekly.md"
reason: "Weekly Instagram post — social batch <timestamp>"
parameters:
  caption: |
    <Instagram caption>
  image_url: ""
timestamp: "<ISO-8601 UTC>"
status: pending
---
**Platform**: Instagram | **Topic**: <topic> | **Words**: <N>
⚠️ Set `image_url` to an image URL or path before approving.
Move to `Approved/` to publish or `Rejected/` to discard.
```

### 5d. Twitter/X Approval

`AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_twitter.md`

```markdown
---
type: approval_request
action: twitter_post
plan_file: "PLAN_<timestamp>_social_weekly.md"
reason: "Weekly Twitter/X post — social batch <timestamp>"
parameters:
  content: |
    <Tweet text>
  is_thread: false
  tweet_count: 1
timestamp: "<ISO-8601 UTC>"
status: pending
---
**Platform**: Twitter/X | **Topic**: <topic> | **Chars**: <N>/280
Move to `Approved/` to publish or `Rejected/` to discard.
```

---

## Step 6 — Log the Batch

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "social_weekly_batch_drafted",
  "actor": "claude_code",
  "target": "all_platforms",
  "parameters": {
    "batch_timestamp": "<timestamp>",
    "topic": "<topic>",
    "plan_file": "PLAN_<timestamp>_social_weekly.md",
    "approval_files": [
      "APPROVAL_<timestamp>_linkedin.md",
      "APPROVAL_<timestamp>_facebook.md",
      "APPROVAL_<timestamp>_instagram.md",
      "APPROVAL_<timestamp>_twitter.md"
    ]
  },
  "approval_status": "deferred",
  "approved_by": "pending",
  "result": "deferred"
}
```

---

## Step 7 — Summary Output

Print a human-readable summary before the completion signal:

```
Weekly Social Batch Ready
-------------------------
Topic: <topic>
Batch ID: <timestamp>

Approval files written to Pending_Approval/:
  ✓ APPROVAL_<timestamp>_linkedin.md   (<N> words)
  ✓ APPROVAL_<timestamp>_facebook.md   (<N> words)
  ✓ APPROVAL_<timestamp>_instagram.md  (<N> words) ⚠️ Add image_url before approving
  ✓ APPROVAL_<timestamp>_twitter.md    (<N>/280 chars)

Review each file in Pending_Approval/ and move to Approved/ or Rejected/.
The execute-plan skill will publish each approved post via social-mcp.
```

---

## Completion Signal

```
<promise>TASK_COMPLETE</promise>
```
