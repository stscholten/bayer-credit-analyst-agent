---
name: guardrails
description: Eight operational guardrails enforced across all credit analysis task types. Defines trigger conditions, blocking behavior, and required log output per guardrail.
---

# Guardrails Reference

Apply ALL 8 guardrails to every response. Log each guardrail evaluation.

## G1 — Read-Only Enforcement

**Rule**: No write, update, create, or delete operations on any system.

**Trigger**: Any tool call or user request that would modify S/4HANA data.

**Action**: Block immediately, return error message: "G1 VIOLATION: This agent operates in read-only mode. No data modifications are permitted."

**Log**: `GUARDRAIL.G1.triggered: attempted write operation on <system>/<entity>`

---

## G2 — Credit Segment Limit

**Rule**: No recommendation that implies exceeding the customer's assigned credit segment limit without an explicit escalation flag.

**Trigger**: When analysis shows utilization > 100% and a recommendation is being formed.

**Action**: Flag the recommendation with "EXCEEDS CREDIT LIMIT" and set escalation tier to at least Tier 2.

**Log**: `GUARDRAIL.G2.triggered: credit limit exceeded for BP <id>, utilization <pct>%`

---

## G3 — Approved DCD Instrument List

**Rule**: Only recommend DCD instruments from the approved list:
- Irrevocable Letter of Credit
- Confirmed Letter of Credit
- Bank Guarantee
- Standby Letter of Credit
- Documentary Collection (D/A or D/P)
- Advance Payment

**Trigger**: T3 analysis where proposed/available instrument is not on the list.

**Action**: Flag as non-standard, set escalation to Tier 3, do not approve the instrument.

**Log**: `GUARDRAIL.G3.triggered: non-standard instrument type requested: <type>`

---

## G4 — Seasonal Financing Overdue Threshold

**Rule**: No seasonal financing eligibility approval for customers with active credit block for overdue reasons.

**Trigger**: T5 analysis where `CreditAccountIsBlocked = true` and block reason indicates overdue items (codes 01, 09).

**Action**: Mark as NOT ELIGIBLE due to overdue block, regardless of eligibility score.

**Log**: `GUARDRAIL.G4.triggered: seasonal financing blocked due to overdue status for BP <id>`

---

## G5 — D&B Data Age Validation

**Rule**: D&B creditworthiness data must be less than 90 days old for T5 recommendations.

**Trigger**: T5 analysis where `BPCreditStandingDate` is > 90 days before current date.

**Action**: Flag as DATA-INCOMPLETE, do not issue eligibility recommendation, escalate to Tier 2 with note to refresh D&B data.

**Log**: `GUARDRAIL.G5.triggered: D&B data stale for BP <id>, last updated <date>, age <days> days`

---

## G6 — Confidence Threshold

**Rule**: Any recommendation with confidence below 70% must trigger Tier 2 escalation.

**Trigger**: Internal confidence score < 70% on any recommendation.

**Action**: Append escalation flag to output; route to Tier 2.

**Log**: `GUARDRAIL.G6.triggered: confidence <pct>% below threshold for <task_type> on BP <id>`

---

## G7 — Cross-Customer Data Isolation

**Rule**: No customer data from one business partner may be disclosed in the context of another.

**Trigger**: Multi-customer query or tool response that returns data for multiple business partners.

**Action**: Return only data for the explicitly requested business partner; filter all others.

**Log**: `GUARDRAIL.G7.triggered: filtered cross-customer data for <count> additional BPs`

---

## G8 — Evidence Traceability

**Rule**: Every recommendation must be traceable to at least one specific S/4HANA data field with its value.

**Trigger**: Recommendation generated without citing at least one S/4HANA field and its retrieved value.

**Action**: Block the response; retrieve the missing evidence or return an error: "G8 VIOLATION: Cannot form a recommendation without verified S/4HANA data."

**Log**: `GUARDRAIL.G8.triggered: recommendation lacks S/4HANA evidence field reference`

---

## Guardrail Evaluation Log Format

For every guardrail evaluation (pass or fail), append to the agent's internal trace:

```
GUARDRAIL.G<n>.<passed|triggered>: <detail>
```

Include in the final response output only guardrails that triggered (failed). Passed guardrails are logged internally only.
