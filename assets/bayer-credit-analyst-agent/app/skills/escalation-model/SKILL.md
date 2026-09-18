---
name: escalation-model
description: Three-tier escalation logic applied to all credit analysis task types (T1-T5). Determines the appropriate escalation tier based on risk signals, confidence, and policy thresholds.
---

# Escalation Model

## Tier Definitions

### Tier 1 — Credit Analyst (No Escalation)
Agent provides full recommendation; analyst acts on it directly.

**Trigger conditions (ALL must be true):**
- Confidence score ≥ 70%
- Risk class is 01 (Low) or 02 (Medium)
- No active credit block for overdue reasons (T5)
- No negative events within last 12 months
- Credit limit utilization < 90% (T2)
- Requested instrument on approved list (T3)
- Payment terms within risk class tolerance (T4)
- No data-incomplete flag (T5: D&B data < 90 days old)

### Tier 2 — Credit Manager (Manager Review)
Agent flags case for Credit Manager review; analyst forwards recommendation.

**Trigger conditions (ANY is sufficient):**
- Confidence score < 70% (Guardrail G6)
- Risk class is 03 (High)
- Credit limit utilization between 90–100% (T2)
- Payment terms BORDERLINE (T4)
- D&B data age > 90 days flag (T5 — Guardrail G5)
- Single negative event within last 12 months
- Seasonal financing eligibility score 50–69 (T5)
- Conflicting data between S/4HANA sources
- Incomplete API data (any required tool call returned error/empty)

### Tier 3 — Credit Committee (Committee Decision)
Agent recommends committee escalation; analyst prepares decision pack.

**Trigger conditions (ANY is sufficient):**
- Risk class is 04 (Critical)
- Credit limit utilization > 100% (T2)
- Requested DCD instrument not on approved list (T3 — Guardrail G3)
- Active D&B alert (bankruptcy signal, legal proceedings initiated)
- Multiple active negative events (≥ 2 within 12 months)
- Customer seasonally financing ineligible (score < 50) AND request for exception
- Policy exception explicitly requested
- High exposure: transaction value > 80% of credit limit (T3/T4)

## Escalation Output Format

Always append the following to any analysis output:

```
---
ESCALATION: TIER <1/2/3>
Authority: <Analyst / Credit Manager / Credit Committee>
Reason: <specific trigger condition that determined the tier>
Action Required: <what the receiving party needs to do>
```

## Task-Type Specific Escalation Notes

- **T1**: If block reason is unknown (code not in reference table), default to Tier 2
- **T2**: Amber utilization (70–90%) stays Tier 1 with monitoring note; Red (>90%) → Tier 2
- **T3**: Any instrument not on approved list → immediate Tier 3
- **T4**: MISMATCH result → Tier 2; COMPLIANT → Tier 1; BORDERLINE → Tier 2
- **T5**: Data-incomplete (stale D&B) → Tier 2; NOT ELIGIBLE score → Tier 2 unless exception requested → Tier 3
