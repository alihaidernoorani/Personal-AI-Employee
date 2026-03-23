---
name: facebook-post
description: |
  Generates a 100-300 word Facebook lead-generation post from Business_Goals.md
  and Company_Handbook.md. Writes a Plan file and an Approval file to
  Pending_Approval/ for human review before publishing. Does NOT call any
  MCP tools -- the boundary is writing the approval file.
  Post contains: value proposition, specific service mention, call-to-action.
  Use this skill on-demand or on a weekly schedule for Facebook social media content.
  Triggered by: "run facebook-post skill", "post to facebook", "create facebook post".
---

# Facebook Post

Generate a Facebook lead-generation post and route it through the approval
pipeline before publishing.

---

## Step 1 -- Read Business Context

Read both source files to understand the business and brand voice:

1. `AI_Employee_Vault/Business_Goals.md` -- services offered, OKRs, post topics
2. `AI_Employee_Vault/Company_Handbook.md` -- brand voice, communication standards, tone

Note the current date to pick a contextually relevant post topic from the
`## LinkedIn Post Topics` section of `Business_Goals.md` (topics apply to all platforms).

---

## Step 2 -- Select a Post Topic

Choose the most relevant topic based on:
- Which topics have NOT been posted to Facebook recently (check `Plans/` for recent Facebook plans)
- Current day/month context (e.g. end-of-quarter for revenue topics)
- Default to the first unused topic if no strong signal exists

---

## Step 3 -- Generate the Post

Write a Facebook post following these requirements:

**Format requirements:**
- Length: 100-300 words
- Must include: value proposition, a specific service/product mention from
  `## Services Offered` in `Business_Goals.md`, and a clear call-to-action (CTA)
- Tone: professional but conversational, per `Company_Handbook.md` brand voice
- Facebook allows more casual, story-driven content than LinkedIn -- slightly warmer tone is fine
- End with 3-5 relevant hashtags
- No emojis unless explicitly permitted in Company_Handbook.md
- Do NOT include any credentials, pricing, or external URLs unless they appear
  in Business_Goals.md

**Post structure:**
1. Opening hook (1-2 sentences that grab attention)
2. Value statement (2-3 sentences about the problem you solve)
3. Service mention (1-2 sentences with a specific service from Business_Goals.md)
4. Social proof or insight (1-2 sentences -- use a realistic placeholder if no real data)
5. Call-to-action (1 sentence: DM, comment, or visit page)
6. Hashtags (3-5 relevant hashtags)

---

## Step 4 -- Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_facebook.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSZ`.

```markdown
---
type: plan
source_task: facebook_post_request
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
topic: "<selected topic title>"
---

## Summary

Facebook post generated from Business_Goals.md topic: <topic title>.

## Post Content

<Full 100-300 word post content here>

## Hashtags

<hashtag1> <hashtag2> <hashtag3> ...

## Notes

Post length: <word count> words
Service referenced: <service name from Business_Goals.md>
CTA type: <DM / comment / visit page>
```

---

## Step 5 -- Write Approval File

Create `AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_facebook.md`
using the same `<timestamp>` as the Plan file.

```markdown
---
type: approval_request
action: facebook_post
plan_file: "PLAN_<timestamp>_facebook.md"
reason: "Weekly Facebook lead-generation post per Business_Goals.md schedule"
parameters:
  post_content: |
    <Full post content -- identical to Plan file content>
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

Publishing to Facebook is an external, irreversible action. Human review
ensures the content is accurate, on-brand, and appropriately timed.

## Action Summary

**Platform**: Facebook
**Post length**: <word count> words
**Topic**: <topic title>
**Action**: Move this file to `Approved/` to publish, or `Rejected/` to discard.
```

---

## Step 6 -- Execute (after approval)

When `APPROVAL_<timestamp>_facebook.md` is moved to `AI_Employee_Vault/Approved/`,
call the social MCP tool directly:

```
mcp__social-mcp__post_facebook
  message: <post_content from approval file parameters.post_content>
```

**Required `.env` keys:**

| Key | Description |
|-----|-------------|
| `FACEBOOK_APP_ID` | OAuth app ID from Facebook Developer Portal |
| `FACEBOOK_APP_SECRET` | OAuth app secret |
| `FACEBOOK_ACCESS_TOKEN` | Long-lived Page Access Token from /me/accounts |
| `FACEBOOK_PAGE_ID` | Numeric Page ID from /me/accounts response |

---

## Step 7 -- Update Dashboard.md

Update `AI_Employee_Vault/Dashboard.md` pending approvals section:

- Increment `<!-- AI_EMPLOYEE:PENDING_APPROVALS -->` count by 1
- Add the new `APPROVAL_*_facebook.md` filename to `<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST -->`
- Update `<!-- AI_EMPLOYEE:UPDATED -->` to current UTC timestamp

---

## Step 8 -- Log the Action

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "facebook_post_drafted",
  "actor": "claude_code",
  "target": "Facebook",
  "parameters": {
    "plan_file": "<PLAN_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename>",
    "word_count": <number>
  },
  "approval_status": "deferred",
  "approved_by": "pending",
  "result": "deferred"
}
```

---

## Completion Signal

When the Plan file, Approval file, Dashboard update, and log entry are all
written, output exactly:

```
<promise>TASK_COMPLETE</promise>
```
