---
type: approval_request
action: social_post
plan_file: "PLAN_20260627T120600Z_LINKEDIN_post_lead-gen.md"
reason: "Publish LinkedIn post: AI automation transforming small business operations"
parameters:
  platform: "linkedin"
  content: |
    🤖 How AI automation is transforming small business operations

    Last week, a client asked me: "Can AI really handle my email inbox, bank transactions, and social media — all at once?"

    The answer? Yes — and here's what that looks like in practice:

    ✅ Gmail watcher processes every email within 60 seconds
    ✅ Bank transactions auto-sync to Odoo with a full audit trail
    ✅ Social posts are drafted, approved by a human, then scheduled
    ✅ A CEO briefing lands every Monday morning — automatically

    The key isn't replacing human judgment. It's replacing the *time* spent on routine tasks so humans can focus on decisions that matter.

    Building this with Claude Code + Obsidian has been the most practical AI project I've worked on. DM me if you want to see how it works for your business.

    #AIAutomation #Productivity #SmallBusiness #ClaudeAI
  visibility: "PUBLIC"
  approval_id: "APPROVAL_20260627T120600Z_linkedin_lead-gen-post"
timestamp: "2026-06-27T12:06:00Z"
created: "2026-06-27T12:06:00Z"
status: pending
---

> [!caution] ⏳ Pending Approval — SOCIAL POST (LINKEDIN)
> **Platform**: LinkedIn · **Topic**: AI automation transforming small business (lead-gen post)
> **To approve**: Move this file to `_System/Approved/` · **To reject**: Move this file to `_System/Rejected/`

## Why Approval is Required

Outbound social media post. Per Company Handbook §2, scheduled posts require approval.

## Action Summary

**Platform**: LinkedIn  
**Content**: Lead-generation post about AI automation (see plan for full text)  
**Action**: Move this file to `_System/Approved/` to publish, or `Rejected/` to discard.

```meta-bind-button
id: "approve-APPROVAL-20260627T120600Z-linkedin-lead-gen-post"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "reject-APPROVAL-20260627T120600Z-linkedin-lead-gen-post"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

> [!success] Click **✅ Approve** or **❌ Reject** above — the approval watcher moves this file and runs (or archives) the action automatically. You can still drag it to `_System/Approved/` or `_System/Rejected/` by hand if you prefer.