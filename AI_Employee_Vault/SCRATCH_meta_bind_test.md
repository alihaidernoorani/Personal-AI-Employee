---
status: pending
---
# Meta Bind Button Test Scratch Note

Delete this file after testing.

## Test 1 — createNote (T032)

Click the button below. It should create `SIGNAL_test_trigger.md` in `_System/Needs_Action/`.

```meta-bind-button
id: "test-create-note"
label: "🧪 Test createNote"
style: primary
actions:
  - type: createNote
    folderPath: "_System/Needs_Action"
    fileName: "SIGNAL_test_trigger"
    openNote: false
    openIfAlreadyExists: false
```

**Expected**: File `_System/Needs_Action/SIGNAL_test_trigger.md` appears in file explorer.

---

## Test 2 — updateMetadata (T033)

Click Approve or Reject below. The `status` field in this note's frontmatter should change.

```meta-bind-button
id: "test-update-approved"
label: "✅ Approve"
style: primary
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "approved"
```

```meta-bind-button
id: "test-update-rejected"
label: "❌ Reject"
style: destructive
actions:
  - type: updateMetadata
    bindTarget: "status"
    evaluate: false
    value: "rejected"
```

**Expected**: Clicking Approve changes `status: pending` → `status: approved` in this note's frontmatter.
