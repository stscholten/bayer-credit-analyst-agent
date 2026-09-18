---
name: payment-term-validation
description: Validates agreed payment terms against customer risk profile, identifying plausibility gaps and mis-alignments that could create collection risk.
allowed-tools:
  - get_business_partner_payment_terms
  - get_customer_sales_area_payment_terms
  - get_credit_management_business_partner
  - get_credit_management_account
---

# T4 — Payment Term Validation

## Steps

1. **Retrieve payment terms**: 
   - Call `get_business_partner_payment_terms` with customer number and company code → `PaymentTerms` from `A_CustomerCompany`
   - Call `get_customer_sales_area_payment_terms` with customer, sales org, distribution channel, division → `CustomerPaymentTerms` from `A_CustomerSalesArea`

2. **Retrieve risk profile**: Call `get_credit_management_business_partner` for `CreditRiskClass` and `CreditWorthinessScoreValue`.

3. **Retrieve credit account**: Call `get_credit_management_account` for current block status and credit limit utilization context.

4. **Cross-reference against risk tier tolerance matrix**:

   | Risk Class | Acceptable Payment Terms | Flag if |
   |------------|--------------------------|---------|
   | 01 (Low)   | Net 60 or better         | > Net 90 |
   | 02 (Medium)| Net 30                   | > Net 45 |
   | 03 (High)  | Net 14 or advance        | > Net 30 |
   | 04 (Critical) | Advance payment only  | Any credit terms |

5. **Identify gaps and exceptions**:
   - MISMATCH: Agreed terms more lenient than risk class allows
   - BORDERLINE: Terms at the limit of risk class tolerance
   - COMPLIANT: Terms within policy for risk class

6. **Apply guardrail G8**: Recommendation must reference specific field values (PaymentTerms code, CreditRiskClass).

7. **Compose output**:
   ```
   PAYMENT TERM VALIDATION — T4
   Customer: <BP number> | Company Code: <code>
   Agreed Payment Terms (Company Level): <code>
   Agreed Payment Terms (Sales Area): <code>
   Risk Class: <class> | Score: <value>
   Validation Result: COMPLIANT / MISMATCH / BORDERLINE
   Gap Description: <text if mismatch>
   Recommendation: <text>
   Escalation Tier: <1/2/3>
   Evidence Fields: PaymentTerms, CreditRiskClass, CustomerPaymentTerms
   ```

8. **Determine escalation tier**: Apply escalation-model skill.
