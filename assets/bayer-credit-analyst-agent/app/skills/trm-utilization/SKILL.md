---
name: trm-utilization
description: Evaluates credit limit utilization incorporating Treasury Risk Management exposure data, calculates risk-tiered utilization scoring with headroom analysis.
allowed-tools:
  - get_credit_management_account
  - get_credit_account_collateral
  - get_credit_management_business_partner
---

# T2 — TRM Credit Limit Utilization

## Steps

1. **Retrieve credit account**: Call `get_credit_management_account` with business partner and credit segment to get:
   - `CreditLimitAmount` (approved limit)
   - `CreditLimitCalculatedAmount` (system-calculated limit)
   - `CreditLimitRequestedAmount` (analyst-requested limit)
   - `CreditSegmentCurrency`

2. **Retrieve TRM exposure components**: Call `get_credit_account_collateral` to get collateral and credit insurance amounts that offset gross exposure.

3. **Retrieve risk profile**: Call `get_credit_management_business_partner` for `CreditRiskClass` and `CreditWorthinessScoreValue`.

4. **Calculate utilization**:
   - Net exposure = gross exposure − collateral − credit insurance
   - Utilization % = (net exposure / credit limit) × 100
   - Headroom = credit limit − net exposure

5. **Apply risk-tier interpretation**:
   - Green (0–70%): Standard utilization, within policy
   - Amber (70–90%): Elevated utilization, monitor closely
   - Red (>90%): Critical utilization, Tier 2 escalation required

6. **Apply guardrail G2**: If utilization exceeds limit, flag for escalation; do not recommend exceeding segment limit.

7. **Compose output**:
   ```
   TRM UTILIZATION ANALYSIS — T2
   Customer: <BP number> | Credit Segment: <segment>
   Credit Limit: <amount> <currency>
   Collateral: <amount> | Credit Insurance: <amount>
   Net Exposure: <amount> | Utilization: <pct>%
   Headroom: <amount>
   Risk Class: <class> | Score: <value>
   Status: GREEN/AMBER/RED
   Recommendation: <text>
   Escalation Tier: <1/2/3>
   Evidence Fields: CreditLimitAmount, CreditLimitCalculatedAmount, CreditSegmentCurrency
   ```

8. **Determine escalation tier**: Apply escalation-model skill.
