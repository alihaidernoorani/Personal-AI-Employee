# Data Model: Gold Tier Personal AI Employee

**Phase**: 1 — Design
**Date**: 2026-03-22
**Feature**: 003-gold-ai-employee

---

## Entities

### 1. Task File (`Needs_Action/TYPE_<id>_<timestamp>.md`)

Represents a single inbound event requiring agent action. Written by watchers; never modified after creation.

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | enum | ✅ | `email` \| `whatsapp` \| `file_drop` \| `finance` \| `action_trigger` \| `error` |
| `source` | string | ✅ | Origin system: `gmail`, `whatsapp`, `inbox`, `bank`, `system` |
| `source_id` | string | ✅ | Unique ID from source (e.g. Gmail message ID). Used for idempotency. |
| `created` | ISO-8601Z | ✅ | Timestamp of file creation |
| `priority` | enum | ✅ | `high` \| `medium` \| `low` |
| `subject` | string | ✅ | Human-readable one-line summary |
| `raw_content` | multiline string | ✅ | Full original message or event body |
| `attachments` | list[string] | ❌ | Attachment filenames if any |

**State transitions**:
```
Created in Needs_Action/
  → Moved to In_Progress/local_agent/   (claimed by skill)
  → (stays) while plan + approval written
  → Moved to Done/                       (task complete)
```

**Naming**: `{TYPE}_{source_id}_{YYYYMMDDTHHMMSSZ}.md`
Example: `EMAIL_18f3c2a9b4d1_20260322T083012Z.md`

---

### 2. Plan (`Plans/PLAN_<timestamp>.md`)

Agent-generated action plan. Written by `process-needs-action` skill; read by `execute-plan` skill and human.

| Field | Type | Required | Description |
|---|---|---|---|
| `plan_id` | string | ✅ | `PLAN_<timestamp>` |
| `task_ref` | path | ✅ | Absolute path to source task file (in `In_Progress/` at time of writing) |
| `created` | ISO-8601Z | ✅ | Plan creation timestamp |
| `requires_approval` | boolean | ✅ | Whether an APPROVAL_*.md must be written |
| `approval_category` | enum | ✅ | `email_new_contact` \| `payment` \| `social_post` \| `bulk_email` \| `none` |

Body sections: Objective, Decision Rationale, Actions (checkboxes), Risk Assessment, Completion Criteria.

**Relationships**: one Plan per Task File. Plan references Task File; Approval File references Plan.

**Invariants**:
- A Plan is written before any action is taken
- Once written, a Plan is not deleted or overwritten; only checkboxes are updated
- `requires_approval: false` only valid for actions matching FR-018 auto-approve list

---

### 3. Approval File (`Pending_Approval/APPROVAL_<timestamp>.md`)

Human-review gate for sensitive actions.

| Field | Type | Required | Description |
|---|---|---|---|
| `approval_id` | string | ✅ | `APPROVAL_<timestamp>` |
| `plan_ref` | path | ✅ | Absolute path to `Plans/PLAN_*.md` |
| `action_type` | enum | ✅ | `send_email` \| `linkedin_post` \| `payment` \| `odoo_sync` \| `bulk_email` \| `social_post` |
| `risk_class` | enum | ✅ | `low` \| `medium` \| `high` \| `critical` |
| `requested_at` | ISO-8601Z | ✅ | When approval was requested |
| `status` | enum | ✅ | `pending` \| `approved` \| `rejected` |
| `is_recurring` | boolean | ❌ | For payments: affects auto-approve eligibility |
| `payment_amount` | decimal | ❌ | For payments: evaluated against $50/$100 thresholds |
| `known_payee` | boolean | ❌ | For payments: must be `true` for auto-approve eligibility |

**State transitions**:
```
Written to Pending_Approval/   (status: pending)
  → Moved to Approved/         (human action → ApprovalWatcher triggers execute-plan)
  → Moved to Rejected/         (human action → permanent archive, never executed)
```

**Invariants**:
- No skill may move its own Approval File to `Approved/`
- Files in `Rejected/` are never moved again
- `payment` action_type with `is_recurring: false` OR `payment_amount > 100` OR `known_payee: false` → always `risk_class: high` or `critical`

---

### 4. Audit Log Entry (`Logs/YYYY-MM-DD.json` — NDJSON)

One JSON object per line. Immutable after writing. Append-only.

| Field | Type | Required | Description |
|---|---|---|---|
| `timestamp` | ISO-8601Z | ✅ | Action execution time |
| `action_type` | string | ✅ | `email_send`, `linkedin_post`, `odoo_invoice`, `payment`, `file_move`, `social_summary`, `ceo_briefing`, etc. |
| `actor` | string | ✅ | `claude_code`, `watcher_gmail`, `watcher_whatsapp`, `watcher_finance`, `watcher_fs`, `approval_watcher` |
| `target` | string | ✅ | Recipient, URL, or resource identifier |
| `parameters` | object | ✅ | Action parameters (no credentials) |
| `approval_status` | enum | ✅ | `approved` \| `auto` \| `pending` |
| `approved_by` | enum | ✅ | `human` \| `system` |
| `result` | enum | ✅ | `success` \| `failure` \| `dry_run` |
| `error_message` | string | ❌ | Present on `result: failure` |
| `dry_run` | boolean | ❌ | Present and `true` when `DRY_RUN=true` |

**Retention**: Files deleted after 90 days by orchestrator scheduled cleanup.

---

### 5. CEO Briefing (`Briefings/YYYY-MM-DD_Monday_Briefing.md`)

Weekly business intelligence report. Written by `ceo-briefing` skill.

| Field | Type | Required | Description |
|---|---|---|---|
| `briefing_date` | YYYY-MM-DD | ✅ | Monday date the briefing covers |
| `period_start` | YYYY-MM-DD | ✅ | Start of reporting period (previous Monday) |
| `period_end` | YYYY-MM-DD | ✅ | End of reporting period (Sunday) |
| `generated_at` | ISO-8601Z | ✅ | When the briefing was written |

Body sections: Executive Summary, Revenue Summary (table), Completed This Week, Bottlenecks (table), Cost Optimisation Suggestions, Upcoming Deadlines, Social Media Summary (table).

**Invariants**:
- One briefing per week; if a briefing already exists for the date, it is NOT overwritten (error logged)
- Briefing is generated even if no anomalies found (clean briefing is valid output)
- Social Media Summary section is always present if any social posts occurred during the period

---

### 6. Bank Transaction Row (`Bank_Transactions.md`)

Append-only ledger of financial events.

| Field | Required | Description |
|---|---|---|
| `date` | ✅ | Transaction date (YYYY-MM-DD) |
| `amount` | ✅ | Signed decimal (negative = debit) |
| `currency` | ✅ | ISO 4217 code (e.g. `USD`) |
| `payee` | ✅ | Counterparty name |
| `reference` | ✅ | Bank reference string |
| `category` | ❌ | Agent-assigned category (e.g. `subscription`, `client_payment`, `fee`) |
| `odoo_synced` | ❌ | `true` once synced to Odoo MCP |

---

### 7. Watcher State (`scripts/processed_*.json`)

Idempotency registry. One file per watcher.

| Field | Type | Description |
|---|---|---|
| `source_type` | string | `gmail`, `whatsapp`, `finance` |
| `processed_ids` | list[string] | All source IDs already processed |
| `last_poll` | ISO-8601Z | Timestamp of last successful poll |

**Invariants**:
- IDs are only added, never removed
- File is read at watcher startup; updated after each successful `create_action_file()` call

---

### 8. Loop State File (`In_Progress/local_agent/TASK_<id>.state.json`)

Ralph Wiggum loop control state. Written by orchestrator; updated by stop hook.

| Field | Type | Description |
|---|---|---|
| `prompt` | string | Original task prompt |
| `iteration` | integer | Current iteration count (0-based) |
| `max_iterations` | integer | Configured maximum (default: 10) |
| `task_file` | path | Path to source task file |
| `prior_output` | string \| null | Claude's output from previous iteration |

---

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    TASK STATE MACHINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [EXTERNAL EVENT]                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐   claim-by-move    ┌──────────────────┐    │
│  │ Needs_Action│ ─────────────────▶ │ In_Progress/     │    │
│  │   (watcher) │                    │  local_agent/    │    │
│  └─────────────┘                    └────────┬─────────┘    │
│                                              │ plan written  │
│                                              ▼               │
│                                     ┌────────────────┐       │
│                                     │    Plans/      │       │
│                                     │  PLAN_*.md     │       │
│                                     └────────┬───────┘       │
│                              ┌───────────────┴──────────┐    │
│                        auto  │                          │ sensitive│
│                        approve                    requires_approval│
│                              ▼                          ▼    │
│                     ┌──────────────┐        ┌──────────────────┐│
│                     │ execute-plan │        │ Pending_Approval/ ││
│                     │   (direct)   │        │  APPROVAL_*.md   ││
│                     └──────┬───────┘        └─────────┬────────┘│
│                            │                          │ human    │
│                            │              ┌───────────┤          │
│                            │           Approved/   Rejected/     │
│                            │              │           │          │
│                            │              ▼           ▼          │
│                            │       ┌──────────┐  ┌──────────┐   │
│                            │       │execute-  │  │Rejected/ │   │
│                            │       │plan(MCP) │  │(archive) │   │
│                            │       └────┬─────┘  └──────────┘   │
│                            │            │                        │
│                            └────────────┘                        │
│                                         │                        │
│                                         ▼                        │
│                                   ┌──────────┐                   │
│                                   │  Done/   │                   │
│                                   │ (archive)│                   │
│                                   └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```
