---
type: approval_request
action: odoo_sync
action_type: finance_sync
plan_file: "PLAN_20260627T090130Z_FINANCE_test001_20260627T090000Z.md"
reason: "Sync finance transaction TEST_TXN_001 (New Client Corp, +$150.00) to Odoo"
parameters:
  transaction_id: "TEST_TXN_001"
  amount: "+$150.00"
  payee: "New Client Corp"
  reference: "INV-TEST-001"
  date: "2026-06-27"
  category: "client_payment"
  odoo_action: "create_transaction"
timestamp: "2026-06-27T09:01:30Z"
status: pending
---

## Why Approval is Required

This is a financial action. Per Company_Handbook Human-in-the-Loop Rules (Section 3),
all payment and financial actions require explicit human approval before execution.

The payee "New Client Corp" is a new entity — per Section 2, new payees always require approval.

## Action Summary

**Transaction**: TEST_TXN_001  
**Amount**: +$150.00  
**Payee**: New Client Corp  
**Reference**: INV-TEST-001  
**Odoo Action**: `odoo-mcp create_transaction`  
**Action**: Move this file to `Approved/` to sync to Odoo, or `Rejected/` to discard.
