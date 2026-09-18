---
name: seasonal-financing
description: Assesses customer eligibility for seasonal financing models, combining S/4HANA payment history data with D&B external creditworthiness, with strict data-age validation.
allowed-tools:
  - get_credit_management_account
  - get_creditworthiness
  - get_credit_management_business_partner
  - get_bp_negative_events
---

# T5 — Seasonal Financing Eligibility

## Steps

1. **Retrieve credit account**: Call `get_credit_management_account` for credit limit, block status, and utilization context.

2. **Retrieve D&B creditworthiness**: Call `get_creditworthiness` and **immediately apply guardrail G5**:
   - Check `BPCreditStandingDate` field
   - If date is more than 90 days ago → set `data_age_flag = TRUE`, return data-incomplete warning, and escalate to Tier 2
   - If date is within 90 days → proceed with data

3. **Check overdue balance — guardrail G4**:
   - If `CreditAccountIsBlocked = true` and `CreditAccountBlockReason` indicates overdue items → flag as ineligible
   - Configurable overdue threshold (default: any credit block for overdue reasons disqualifies)

4. **Retrieve negative events**: Call `get_bp_negative_events` and check for any active negative events within the past 12 months.

5. **Retrieve risk profile**: Call `get_credit_management_business_partner` for risk class and score.

6. **Calculate eligibility score** (0–100):
   - Risk Class 01 (Low): +40 points
   - Risk Class 02 (Medium): +25 points
   - Risk Class 03 (High): +10 points
   - Risk Class 04 (Critical): −20 points
   - D&B Rating AAA/AA/A: +30 points
   - D&B Rating BBB/BB/B: +15 points
   - D&B Rating CCC or below: −20 points
   - No overdue block: +20 points
   - Active overdue block: −30 points
   - No negative events (12m): +10 points
   - Active negative events: −20 points

7. **Eligibility decision**:
   - Score ≥ 70: ELIGIBLE — recommend seasonal financing approval
   - Score 50–69: CONDITIONAL — eligible with enhanced monitoring or reduced limit
   - Score < 50: NOT ELIGIBLE — standard payment terms required

8. **Compose output**:
   ```
   SEASONAL FINANCING ELIGIBILITY — T5
   Customer: <BP number>
   D&B Data Age: <date> — VALID / STALE (G5 flag)
   Overdue Status: <clean/blocked> (G4 check)
   Risk Class: <class> | Score: <value>
   D&B Rating: <rating>
   Negative Events (12m): <count>
   Eligibility Score: <score>/100
   Decision: ELIGIBLE / CONDITIONAL / NOT ELIGIBLE
   Key Factors: <list of top positive/negative factors>
   Recommendation: <text>
   Escalation Tier: <1/2/3>
   Evidence Fields: CreditRiskClass, BPCreditStandingDate, CreditAccountIsBlocked, BPCreditStandingRating
   ```

9. **Determine escalation tier**: Apply escalation-model skill.
