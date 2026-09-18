---
name: dcd-decision-support
description: Provides decision support for Documentary Credit Decisions (letters of credit, bank guarantees) by assessing instrument adequacy against customer risk profile.
allowed-tools:
  - get_credit_management_business_partner
  - get_credit_management_account
  - get_creditworthiness
---

# T3 — DCD Decision Support

## Steps

1. **Retrieve business partner risk profile**: Call `get_credit_management_business_partner` for:
   - `CreditRiskClass`
   - `CreditCheckRule`
   - `CreditWorthinessScoreValue`
   - `CrdtWrthnssScoreValdtyEndDate`

2. **Retrieve credit account**: Call `get_credit_management_account` for credit limit and current utilization context.

3. **Retrieve creditworthiness**: Call `get_creditworthiness` for any external creditworthiness data including legal proceedings status.

4. **Assess DCD instrument type**: Based on the customer's risk class and transaction context, evaluate whether the proposed or available instrument type is adequate:
   - Risk Class Low: Open account terms may be acceptable
   - Risk Class Medium: Bank guarantee or confirmed LC recommended
   - Risk Class High: Irrevocable confirmed letter of credit required
   - Risk Class Critical: Advance payment or documentary credit with first-class bank

5. **Apply guardrail G3**: Only recommend instruments on the approved instrument list:
   - Irrevocable Letter of Credit (LC)
   - Confirmed Letter of Credit
   - Bank Guarantee
   - Standby Letter of Credit
   - Documentary Collection (D/A or D/P)
   - Advance Payment
   If instrument requested is not on this list, flag as non-standard and escalate to Tier 2.

6. **Evaluate coverage adequacy**: Check if instrument amount covers the transaction value plus standard risk buffer.

7. **Compose output**:
   ```
   DCD DECISION SUPPORT — T3
   Customer: <BP number>
   Risk Class: <class> | Score: <value>
   Proposed Instrument: <type>
   Adequacy Assessment: ADEQUATE / INADEQUATE / MARGINAL
   Recommended Instrument: <type>
   Coverage: <amount> vs. Transaction: <amount>
   Legal Proceedings: <status>
   Recommendation: <text>
   Escalation Tier: <1/2/3>
   Evidence Fields: CreditRiskClass, CreditWorthinessScoreValue, BPLegalProceedingStatus
   ```

8. **Determine escalation tier**: Apply escalation-model skill.
