# 🤖 AI Employee — Control Center

> **Platinum v0.4** · Claude Sonnet 4.6 · Last updated: <!-- AI_EMPLOYEE:UPDATED -->2026-06-28T08:15:00Z<!-- /AI_EMPLOYEE:UPDATED -->

> [!todo] **Decision Queue** &nbsp; ✋ <!-- AI_EMPLOYEE:PENDING_APPROVALS -->13<!-- /AI_EMPLOYEE:PENDING_APPROVALS --> awaiting approval &nbsp;·&nbsp; 📬 <!-- AI_EMPLOYEE:NEEDS_ACTION_COUNT -->5<!-- /AI_EMPLOYEE:NEEDS_ACTION_COUNT --> needs action &nbsp;·&nbsp; 📥 <!-- AI_EMPLOYEE:INBOX_COUNT -->0<!-- /AI_EMPLOYEE:INBOX_COUNT --> inbox &nbsp;·&nbsp; ✅ <!-- AI_EMPLOYEE:DONE_TODAY_COUNT -->0<!-- /AI_EMPLOYEE:DONE_TODAY_COUNT --> done today

---

## ✋ Approvals — Approve or Reject

> [!caution] These drafts are **blocked until you decide**. Click **✅ Approve** or **❌ Reject** beside any item below for a one-click decision, or open a row in the table to read the full draft first. Approving sends/executes the action; rejecting archives it to `_System/Rejected/` (never deleted).

### 📋 Live Decision Table

```dataview
TABLE WITHOUT ID
  ("**" + choice(action = "send_email", "📧 Email", choice(action = "social_post", "📣 Social", choice(action = "reconcile_transaction", "💰 Finance", "📄 Other"))) + "**") AS "Type",
  reason AS "What it does",
  dateformat(file.ctime, "MMM dd, HH:mm") AS "Requested",
  file.link AS "Open"
FROM "_System/Pending_Approval"
WHERE type = "approval_request" AND status = "pending"
SORT file.ctime ASC
```

### ⚡ One-Click Decisions

<!-- AI_EMPLOYEE:PENDING_APPROVAL_LIST -->

#### 💰 Finance · 7 awaiting

_Highest-impact first. Approving reconciles the transaction in Odoo._

| Transaction | Amount | Approve / Reject |
|:--- |:--- |:---:|
| 💵 [[_System/Pending_Approval/APPROVAL_20260627T120001Z_finance_TXN001\|Acme Corp Ltd]] · INV-2026-010 | **+$4,500.00** | `BUTTON[ap-fin-txn001]` `BUTTON[rj-fin-txn001]` |
| 💵 [[_System/Pending_Approval/APPROVAL_20260627T120003Z_finance_TXN003\|TechStart]] | **+$2,800.00** | `BUTTON[ap-fin-txn003]` `BUTTON[rj-fin-txn003]` |
| 💵 [[_System/Pending_Approval/APPROVAL_20260627T120005Z_finance_TXN005\|New Lead]] | **+$1,200.00** | `BUTTON[ap-fin-txn005]` `BUTTON[rj-fin-txn005]` |
| 💳 [[_System/Pending_Approval/APPROVAL_20260627T120004Z_finance_TXN004\|AWS]] | **−$89.50** | `BUTTON[ap-fin-txn004]` `BUTTON[rj-fin-txn004]` |
| 💳 [[_System/Pending_Approval/APPROVAL_20260627T120002Z_finance_TXN002\|Adobe]] | **−$59.99** | `BUTTON[ap-fin-txn002]` `BUTTON[rj-fin-txn002]` |
| 🧪 [[_System/Pending_Approval/APPROVAL_20260627T090130Z_finance_TEST_TXN_001\|Test TXN 001]] | _test_ | `BUTTON[ap-fin-test001]` `BUTTON[rj-fin-test001]` |
| 🧪 [[_System/Pending_Approval/APPROVAL_20260627T123502Z_finance_T073\|T073 Smoke Test]] | _test_ | `BUTTON[ap-fin-t073]` `BUTTON[rj-fin-t073]` |

#### 📧 Email · 4 awaiting

_Approving sends the reply via the Email MCP._

| Reply | To | Approve / Reject |
|:--- |:--- |:---:|
| ✉️ [[_System/Pending_Approval/APPROVAL_20260321T180000Z_email_bilal-client-example-com\|Re: March Payment Confirmation]] | bilal.client | `BUTTON[ap-email-bilal]` `BUTTON[rj-email-bilal]` |
| ✉️ [[_System/Pending_Approval/APPROVAL_20260320T120011Z_email_alihaidernoorani-yahoo-com\|Invoice Reminder Reply]] | alihaidernoorani | `BUTTON[ap-email-invrem]` `BUTTON[rj-email-invrem]` |
| ✉️ [[_System/Pending_Approval/APPROVAL_20260321T120001Z_email_scheduler-test-example-com\|Scheduler Test Reply]] | scheduler-test | `BUTTON[ap-email-sched]` `BUTTON[rj-email-sched]` |
| ✉️ [[_System/Pending_Approval/APPROVAL_20260627T123500Z_email_smoketest-example-com\|Smoke Test Reply]] | smoketest | `BUTTON[ap-email-smoke]` `BUTTON[rj-email-smoke]` |

#### 📣 Social Media · 2 awaiting

_Approving publishes the post to the platform._

| Post | Platform | Approve / Reject |
|:--- |:--- |:---:|
| 🔗 [[_System/Pending_Approval/APPROVAL_20260627T120600Z_linkedin_lead-gen-post\|Lead-Gen Post]] | LinkedIn | `BUTTON[ap-social-leadgen]` `BUTTON[rj-social-leadgen]` |
| 🔗 [[_System/Pending_Approval/APPROVAL_20260323T120000Z_linkedin\|AI Automation Post]] | LinkedIn | `BUTTON[ap-social-aiauto]` `BUTTON[rj-social-aiauto]` |

<!-- /AI_EMPLOYEE:PENDING_APPROVAL_LIST -->

> [!tip] One click sets the draft's `status` field; the approval watcher then moves it to `_System/Approved/` (sends/executes) or `_System/Rejected/` (archives). Prefer to read first? Click the item link or the **Open** column in the table above — each file has the same Approve/Reject buttons inside.

#### 🗑️ Recent Rejections

<!-- AI_EMPLOYEE:RECENT_REJECTIONS -->
_No recent rejections._
<!-- /AI_EMPLOYEE:RECENT_REJECTIONS -->

---

## 📬 Needs Action

> [!warning] Tasks the AI has queued for you. Errors (`ERROR_*`) are hidden from this list and surfaced in System Status.

<!-- AI_EMPLOYEE:ACTIVE_ITEMS -->
- TASK_20260625T090000Z_client-q3-proposal
- TASK_20260624T140000Z_subscription-audit
- PROVISION_SMOKE_TEST_20260628T042706Z
- PROVISION_SMOKE_TEST_20260628T045436Z
- PROVISION_SMOKE_TEST_20260628T050800Z
<!-- /AI_EMPLOYEE:ACTIVE_ITEMS -->

```dataview
TABLE WITHOUT ID
  file.link AS "Task",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") AS "Received"
FROM "_System/Needs_Action"
WHERE !(startswith(file.name, "ERROR_"))
SORT file.mtime ASC
```

---

## ⚡ Quick Actions

> [!example] Click any button to queue a new task. The AI drafts it, then it returns here for your approval.

| 📨 Communications | 📣 Social Media | 💼 Business |
|:---:|:---:|:---:|
| `BUTTON[trigger-email]` | `BUTTON[trigger-linkedin]` | `BUTTON[trigger-invoice]` |
| `BUTTON[trigger-whatsapp]` | `BUTTON[trigger-facebook]` | `BUTTON[trigger-briefing]` |
| &nbsp; | `BUTTON[trigger-instagram]` | &nbsp; |
| &nbsp; | `BUTTON[trigger-twitter]` | &nbsp; |

---

## 💰 Finance Snapshot

> [!info] June 2026 — Income: **+$8,500.00** · Expenses: **−$149.49** · Net: **+$8,350.51**
> Full log: [[Bank_Transactions]] · [[Accounting/Current_Month]]

---

## ✅ Recent Completions

<!-- AI_EMPLOYEE:RECENT_COMPLETIONS -->
_Updated by process-needs-action skill on next run._
<!-- /AI_EMPLOYEE:RECENT_COMPLETIONS -->

```dataview
LIST WITHOUT ID file.link
FROM "_System/Done"
SORT file.mtime DESC
LIMIT 10
```

---

## 📋 Compliance

> [!abstract] Platinum Compliance Gate

<!-- AI_EMPLOYEE:COMPLIANCE_STATUS -->
- **Result**: <!-- AI_EMPLOYEE:COMPLIANCE_RESULT -->PARTIAL<!-- /AI_EMPLOYEE:COMPLIANCE_RESULT -->
- **Last checked**: <!-- AI_EMPLOYEE:COMPLIANCE_DATE -->2026-06-28<!-- /AI_EMPLOYEE:COMPLIANCE_DATE -->
- **Report**: <!-- AI_EMPLOYEE:COMPLIANCE_REPORT -->[[Briefings/COMPLIANCE_REPORT_2026-06-28|📄 View Full Compliance Report]]<!-- /AI_EMPLOYEE:COMPLIANCE_REPORT -->
- **Principles**: <!-- AI_EMPLOYEE:COMPLIANCE_COUNTS -->Pass: 7, Fail: 0, Manual: 8<!-- /AI_EMPLOYEE:COMPLIANCE_COUNTS -->
<!-- /AI_EMPLOYEE:COMPLIANCE_STATUS -->

---

## 🔗 Quick Navigation

> [!note] Vault Links
> [[Pipeline|🗂️ Pipeline]] · [[Briefings/|📊 Briefings]] · [[Bank_Transactions|💰 Transactions]] · [[Accounting/Current_Month|🧾 Current Month]] · [[Reference/Company_Handbook|📖 Handbook]] · [[Reference/Business_Goals|💼 Goals]]

---

## 🖥️ System Status

> [!success]- ✅ File Watcher · ONLINE
> Monitoring `_System/Inbox/` and `_System/Needs_Action/` · Last check: `2026-03-22T08:00 UTC`

> [!success]- ✅ Gmail Watcher · ONLINE
> Monitoring inbox for new messages · Last check: `2026-03-22T08:00 UTC`

> [!success]- ✅ WhatsApp Watcher · ONLINE
> Receive-only mode (Silver tier) · Last check: `2026-03-22T07:11 UTC`

> [!warning]- ⏸ Approval Watcher · STOPPED
> Not running · Start orchestrator to auto-process `_System/Approved/` folder

> [!success]- ✅ Vault Sync (Syncthing) · ACTIVE
> Bi-directional sync running · Last sync: `2026-03-22T08:00 UTC`

---

## ☁️ Cloud Agent Status

> [!info]- Cloud Agent Details
> **Cloud Status**: <!-- AI_EMPLOYEE:CLOUD_STATUS -->UNKNOWN<!-- /AI_EMPLOYEE:CLOUD_STATUS -->
>
> **Agent**: <!-- AI_EMPLOYEE:CLOUD_AGENT_STATUS -->NOT_CONFIGURED<!-- /AI_EMPLOYEE:CLOUD_AGENT_STATUS --> · Last heartbeat: <!-- AI_EMPLOYEE:CLOUD_LAST_HEARTBEAT -->—<!-- /AI_EMPLOYEE:CLOUD_LAST_HEARTBEAT -->
>
> **Cloud Watcher**: <!-- AI_EMPLOYEE:CLOUD_WATCHER_STATUS -->NOT_RUNNING<!-- /AI_EMPLOYEE:CLOUD_WATCHER_STATUS -->
>
> **Vault Sync Last OK**: <!-- AI_EMPLOYEE:VAULT_SYNC_LAST_OK -->2026-03-22T08:00 UTC<!-- /AI_EMPLOYEE:VAULT_SYNC_LAST_OK -->

<!-- AI_EMPLOYEE:IN_PROGRESS_CLOUD -->
_No cloud tasks in progress._
<!-- /AI_EMPLOYEE:IN_PROGRESS_CLOUD -->

<!-- AI_EMPLOYEE:IN_PROGRESS_LOCAL -->
_No local tasks in progress._
<!-- /AI_EMPLOYEE:IN_PROGRESS_LOCAL -->

<!-- AI_EMPLOYEE:CLOUD_RECENT_UPDATES -->
_No recent cloud updates._
<!-- /AI_EMPLOYEE:CLOUD_RECENT_UPDATES -->

---

## 🗒️ Activity Log

> [!note]- 2026-06-28 — Dashboard Redesign
> Rebuilt the Approvals section as the primary surface: live Dataview decision table + grouped one-click Approve/Reject (Finance → Email → Social) with amounts and recipients surfaced inline. Moved all hidden Meta Bind button definitions to a collapsed appendix so the body reads clean. All 22 AI_EMPLOYEE markers preserved.

> [!note]- 2026-06-28 — Dashboard UX Pass
> Pending Approvals reorganized into Email / Social / Finance draft sections with inline ✅/❌ buttons. Fixed Meta Bind error (invalid `secondary` style → `default`). Approval watcher now reacts to button-driven `status` changes.

> [!note]- 2026-06-28 — Platinum Phase 10 Complete
> All 54 Platinum tasks done (T001–T054). Constitution check: **7 PASS · 0 FAIL · 8 MANUAL**. README updated with Lessons Learned. Platinum gate: **PASS**. PHR written to `history/prompts/004-platinum-ai-employee/`.

> [!note]- 2026-06-27 — Gold Tier Fully Operational
> 76/76 Gold tasks complete (T001–T076). Odoo INV/2026/00010 posted live ($4,500 Acme Corp). ⚠️ Email OAuth2 expired — renew `.gmail_mcp_token.json`. ⚠️ LinkedIn auth expired (60d).

> [!note]- 2026-06-26 — CEO Briefing Generated
> [[Briefings/2026-06-26_Monday_Briefing]] created. ⚠️ Facebook token expired — refresh `FACEBOOK_ACCESS_TOKEN`. LinkedIn approval pending 95+ days.

> [!note]- 2026-03-22 — Silver Tier Operational
> 3 WhatsApp messages processed (Mummy, Muazz Tahir, Saad Ahmed Rentals). All logged — Silver tier is receive-only. 4 approvals pending sign-off.

> [!note]- Bronze Tier — All Criteria Verified
> SC-001 ✅ · SC-002 ✅ · SC-003 ✅ · SC-004 ✅ · SC-005 ✅ · SC-006 ✅

---

> [!example]- 🔧 Button Definitions (do not edit — power the Quick Actions and Approve/Reject controls above)
> These hidden Meta Bind buttons render where they are referenced with `BUTTON[id]`. Trigger buttons create a `SIGNAL_*` task in `_System/Needs_Action/`; Approve/Reject buttons set `status` in the target file, after which the approval watcher moves it to `_System/Approved/` or `_System/Rejected/` and fires the workflow.

```meta-bind-button
id: "trigger-email"
hidden: true
label: "📧 Reply to Email"
style: primary
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_email_request"
    openNote: false
```
```meta-bind-button
id: "trigger-whatsapp"
hidden: true
label: "💬 Reply to WhatsApp"
style: primary
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_whatsapp_request"
    openNote: false
```
```meta-bind-button
id: "trigger-linkedin"
hidden: true
label: "📣 Post on LinkedIn"
style: default
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_linkedin_post"
    openNote: false
```
```meta-bind-button
id: "trigger-facebook"
hidden: true
label: "📘 Post on Facebook"
style: default
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_facebook_post"
    openNote: false
```
```meta-bind-button
id: "trigger-instagram"
hidden: true
label: "📸 Post on Instagram"
style: default
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_instagram_post"
    openNote: false
```
```meta-bind-button
id: "trigger-twitter"
hidden: true
label: "🐦 Post on Twitter/X"
style: default
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_twitter_post"
    openNote: false
```
```meta-bind-button
id: "trigger-invoice"
hidden: true
label: "💰 Create Invoice"
style: primary
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_invoice_create"
    openNote: false
```
```meta-bind-button
id: "trigger-briefing"
hidden: true
label: "📊 Run CEO Briefing"
style: primary
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_ceo_briefing"
    openNote: false
```
```meta-bind-button
id: "ap-email-bilal"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260321T180000Z_email_bilal-client-example-com#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-email-bilal"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260321T180000Z_email_bilal-client-example-com#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-email-invrem"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260320T120011Z_email_alihaidernoorani-yahoo-com#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-email-invrem"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260320T120011Z_email_alihaidernoorani-yahoo-com#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-email-sched"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260321T120001Z_email_scheduler-test-example-com#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-email-sched"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260321T120001Z_email_scheduler-test-example-com#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-email-smoke"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T123500Z_email_smoketest-example-com#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-email-smoke"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T123500Z_email_smoketest-example-com#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-social-leadgen"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120600Z_linkedin_lead-gen-post#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-social-leadgen"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120600Z_linkedin_lead-gen-post#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-social-aiauto"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260323T120000Z_linkedin#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-social-aiauto"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260323T120000Z_linkedin#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-txn001"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120001Z_finance_TXN001#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-txn001"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120001Z_finance_TXN001#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-txn002"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120002Z_finance_TXN002#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-txn002"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120002Z_finance_TXN002#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-txn003"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120003Z_finance_TXN003#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-txn003"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120003Z_finance_TXN003#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-txn004"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120004Z_finance_TXN004#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-txn004"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120004Z_finance_TXN004#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-txn005"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120005Z_finance_TXN005#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-txn005"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T120005Z_finance_TXN005#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-test001"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T090130Z_finance_TEST_TXN_001#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-test001"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T090130Z_finance_TEST_TXN_001#status"
    evaluate: false
    value: "rejected"
```
```meta-bind-button
id: "ap-fin-t073"
hidden: true
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T123502Z_finance_T073#status"
    evaluate: false
    value: "approved"
```
```meta-bind-button
id: "rj-fin-t073"
hidden: true
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "_System/Pending_Approval/APPROVAL_20260627T123502Z_finance_T073#status"
    evaluate: false
    value: "rejected"
```
