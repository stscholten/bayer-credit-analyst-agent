---
name: credit-block-analysis
description: Analyzes blocked sales orders and customers, identifies triggered credit rules, and generates plain-language explanations with supporting S/4HANA data.
allowed-tools:
  - get_credit_management_account
  - get_blocked_sales_documents
  - get_blocked_sales_document_by_id
  - get_credit_management_business_partner
---

# T1 — Credit Block Explanation

## Steps

1. **Retrieve blocked documents**: Call `get_blocked_sales_documents` with the sold-to party number. Filter results to documents with `TotalCreditCheckStatus` != "A" (not approved).

2. **Retrieve credit account**: Call `get_credit_management_account` with the business partner and credit segment to get:
   - `CreditAccountIsBlocked` (bool)
   - `CreditAccountBlockReason` (code)
   - `CreditLimitAmount`
   - `CreditLimitValidityEndDate`
   - `CreditLimitCalculatedAmount`

3. **Retrieve business partner risk profile**: Call `get_credit_management_business_partner` to get:
   - `CreditRiskClass`
   - `CreditCheckRule`
   - `CreditWorthinessScoreValue`
   - `CrdtWrthnssScoreValdtyEndDate`

4. **Identify credit rule triggers**: Map `CreditAccountBlockReason` code to plain-language explanation using the lookup table below.

5. **Apply guardrails**:
   - G1: No write operations permitted
   - G8: Every explanation must reference at least one specific S/4HANA field name and its value

6. **Compose output**:
   ```
   CREDIT BLOCK ANALYSIS — T1
   Customer: <BP number>
   Block Reason: <code> — <plain-language description>
   Credit Limit: <amount> <currency> (valid until <date>)
   Calculated Limit: <amount>
   Risk Class: <class>
   Credit Check Rule: <rule>
   Score: <value> (valid until <date>)
   Affected Documents: <count> sales orders totaling <amount>
   Recommendation: <text>
   Escalation Tier: <1/2/3>
   Evidence Fields: CreditAccountBlockReason, CreditLimitAmount, CreditRiskClass
   ```

7. **Determine escalation tier**: Apply escalation-model skill.

## Block Reason Code Reference

| Code | Plain-Language Explanation |
|------|---------------------------|
| 01   | Credit limit exceeded — outstanding receivables exceed the approved credit limit |
| 02   | Credit limit validity expired — the credit limit has passed its valid-to date |
| 03   | Critical customer flag — customer is marked for special attention |
| 04   | Risk class block — customer's risk class requires manual credit approval |
| 05   | Negative event recorded — a negative credit event (e.g. bankruptcy signal) is on record |
| 06   | Missing credit information — mandatory credit data is incomplete |
| 07   | Manual block — credit analyst has placed a manual hold on the account |
| 08   | Financial document check failed — required documentary credit instrument is missing or expired |
| 09   | Overdue items — customer has open items past due date exceeding tolerance |
| 10   | New customer — first-order block pending initial credit assessment |
| (other) | Credit block — reason code not in standard lookup; refer to SAP Credit Management configuration |
