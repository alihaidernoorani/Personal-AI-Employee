---
name: instagram-post
description: |
  Generates an Instagram post (caption 100-300 words + image prompt) from
  Business_Goals.md and Company_Handbook.md. Writes a Plan file and an
  Approval file to Pending_Approval/ for human review before publishing.
  Does NOT call any MCP tools — the boundary is writing the approval file.
  Post contains: value proposition, specific service mention, call-to-action,
  and a descriptive image prompt so the owner can source or generate an image.
  Use this skill on-demand or on a weekly schedule for Instagram content.
  Triggered by: "run instagram-post skill", "post to instagram", "create instagram post".
---

# Instagram Post

Generate an Instagram caption and image prompt, then route through the
approval pipeline before publishing.

---

## Step 1 — Read Business Context

Read both source files:

1. `AI_Employee_Vault/Business_Goals.md` — services offered, OKRs, post topics
2. `AI_Employee_Vault/Company_Handbook.md` — brand voice, communication standards, tone

Note the current date to pick a contextually relevant topic from
`## LinkedIn Post Topics` (topics apply to all platforms) in `Business_Goals.md`.

---

## Step 2 — Select a Post Topic

Choose the most relevant topic based on:
- Which topics have NOT been posted to Instagram recently (check `Plans/` for recent Instagram plans)
- Current day/month context
- Default to the first unused topic if no strong signal exists

---

## Step 3 — Generate the Caption and Image Prompt

### Caption requirements:
- Length: 100–300 words
- Must include: value proposition, specific service mention from `Business_Goals.md`, clear call-to-action
- Tone: conversational and visual — Instagram favours storytelling over corporate speak
- End with 5–10 relevant hashtags (Instagram allows up to 30; use the most targeted)
- No external URLs in caption — Instagram does not make links clickable; direct to "link in bio"
- No emojis unless explicitly permitted in `Company_Handbook.md`

### Caption structure:
1. Opening hook (1–2 sentences — start with a question or bold statement)
2. Value statement (2–3 sentences about the problem you solve)
3. Service mention (1–2 sentences with a specific service from `Business_Goals.md`)
4. Social proof or insight (1–2 sentences)
5. Call-to-action (1 sentence: DM, comment, or "link in bio")
6. Line break then hashtags (5–10 targeted hashtags)

### Image prompt (required):
Write a 2–4 sentence description of the ideal image to accompany this post.
This is NOT an AI prompt — it's guidance for the owner to source or create
a photo/graphic. Example: "A professional photo of a laptop and notebook on
a clean desk, natural lighting, warm tones. No people visible. Suitable for
a B2B service brand."

---

## Step 4 — Write Plan File

Create `AI_Employee_Vault/Plans/PLAN_<timestamp>_instagram.md` where
`<timestamp>` is the current UTC time as `YYYYMMDDTHHMMSSZ`.

```markdown
---
type: plan
source_task: instagram_post_request
created_at: <ISO-8601 UTC timestamp>
requires_approval: true
status: awaiting_approval
topic: "<selected topic title>"
---

## Summary

Instagram post generated from Business_Goals.md topic: <topic title>.

## Caption

<Full 100-300 word caption here>

## Hashtags

<hashtag1> <hashtag2> ... <hashtag10>

## Image Prompt

<2-4 sentence image description for the owner to source>

## Notes

Caption length: <word count> words
Service referenced: <service name from Business_Goals.md>
CTA type: <DM / comment / link in bio>
```

---

## Step 5 — Write Approval File

Create `AI_Employee_Vault/Pending_Approval/APPROVAL_<timestamp>_instagram.md`
using the same `<timestamp>` as the Plan file.

```markdown
---
type: approval_request
action: instagram_post
plan_file: "PLAN_<timestamp>_instagram.md"
reason: "Instagram lead-generation post per Business_Goals.md schedule"
parameters:
  caption: |
    <Full caption — identical to Plan file content>
  image_url: ""
timestamp: "<ISO-8601 UTC>"
status: pending
---

## Why Approval is Required

Publishing to Instagram is an external, irreversible action. Human review
ensures the content is accurate, on-brand, and accompanied by an approved image.

## Action Required Before Approving

1. Source or generate an image matching the Image Prompt in the Plan file
2. Set the `image_url` field above to the URL or local path of that image
3. Move this file to `Approved/` to publish, or `Rejected/` to discard

## Action Summary

**Platform**: Instagram
**Caption length**: <word count> words
**Topic**: <topic title>
```

---

## Step 6 — Execute (after approval)

When `APPROVAL_<timestamp>_instagram.md` is moved to `AI_Employee_Vault/Approved/`,
the `execute-plan` skill calls:

```
mcp__social-mcp__post_instagram
  caption: <caption from approval file parameters.caption>
  image_url: <image_url from approval file parameters.image_url>
  approval_id: <approval filename stem>
```

**Required `.env` keys:**

| Key | Description |
|-----|-------------|
| `INSTAGRAM_ACCESS_TOKEN` | Instagram Graph API token (via Facebook Developer Portal) |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Business Account ID from /me/accounts |

**Note:** Instagram Graph API requires a Business or Creator account linked to a Facebook Page.
Personal accounts cannot post via the API.

---

## Step 7 — Log the Action

Append one NDJSON line to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "<ISO-8601Z>",
  "action_type": "instagram_post_drafted",
  "actor": "claude_code",
  "target": "Instagram",
  "parameters": {
    "plan_file": "<PLAN_*.md filename>",
    "approval_file": "<APPROVAL_*.md filename>",
    "word_count": 0
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
