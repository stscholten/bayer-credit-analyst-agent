# Specification: bayer-credit-analyst-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md` in the solution root for full context
- [ ] Bootstrap agent code in `assets/bayer-credit-analyst-agent/` using the sap-agent-bootstrap instructions (invoke from inside `assets/bayer-credit-analyst-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/credit-block-analysis/SKILL.md` for T1 task type:
  - Frontmatter: `name: credit-block-analysis`, `description: Analyzes blocked sales orders and customers, identifies triggered credit rules, and generates plain-language explanations with supporting S/4HANA data.`, `allowed-tools: [get_credit_management_account, get_blocked_sales_documents, get_business_partner_risk_profile]`
  - Body: Step-by-step instructions for credit block analysis: retrieve blocked documents → identify credit rule triggers → fetch credit account data → cross-reference risk category → compose explanation with evidence fields → apply guardrails G1/G2/G8 → determine escalation tier
  - Include lookup table for credit block reason codes and their plain-language explanations

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/trm-utilization/SKILL.md` for T2 task type:
  - Frontmatter: `name: trm-utilization`, `description: Evaluates credit limit utilization incorporating Treasury Risk Management exposure data, calculates risk-tiered utilization scoring.`, `allowed-tools: [get_credit_management_account, get_credit_account_collateral, get_business_partner_risk_profile]`
  - Body: Retrieve credit limit → retrieve current utilization → incorporate TRM exposure components (collateral, insurance) → calculate utilization % and headroom → apply risk-tier interpretation (green/amber/red) → compose output with evidence → apply guardrail G2 → determine escalation tier

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/dcd-decision-support/SKILL.md` for T3 task type:
  - Frontmatter: `name: dcd-decision-support`, `description: Provides decision support for Documentary Credit Decisions (letters of credit, bank guarantees) by assessing instrument adequacy against customer risk profile.`, `allowed-tools: [get_business_partner_risk_profile, get_credit_management_account, get_creditworthiness]`
  - Body: Retrieve customer risk profile → assess current instrument type in context → evaluate coverage adequacy → cross-reference approved instrument list (guardrail G3) → compose structured recommendation with risk factors and evidence → determine escalation tier

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/payment-term-validation/SKILL.md` for T4 task type:
  - Frontmatter: `name: payment-term-validation`, `description: Validates agreed payment terms against customer risk profile, identifying plausibility gaps and mis-alignments that could create collection risk.`, `allowed-tools: [get_business_partner_payment_terms, get_business_partner_risk_profile, get_credit_management_account]`
  - Body: Retrieve agreed payment terms (from CustomerSalesArea/CustomerCompany) → retrieve risk class and credit score → cross-reference payment term against risk tier tolerance matrix → identify gaps and exceptions → compose recommendation with flag severity → apply guardrail G8 → determine escalation tier

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/seasonal-financing/SKILL.md` for T5 task type:
  - Frontmatter: `name: seasonal-financing`, `description: Assesses customer eligibility for seasonal financing models, combining S/4HANA payment history data with D&B external creditworthiness.`, `allowed-tools: [get_credit_management_account, get_creditworthiness, get_business_partner_risk_profile, check_overdue_balance]`
  - Body: Retrieve S/4HANA payment history and open items → retrieve D&B creditworthiness data → validate D&B data age (guardrail G5 — flag if >90 days) → calculate eligibility score based on: payment history, risk class, overdue balance (guardrail G4), D&B rating → compose eligibility recommendation with score and key factors → determine escalation tier

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/escalation-model/SKILL.md`:
  - Frontmatter: `name: escalation-model`, `description: Three-tier escalation logic for all credit analysis task types.`
  - Body: Define escalation tiers — Tier 1 (analyst, standard confidence/risk), Tier 2 (credit manager, moderate risk/conflicting data/borderline/confidence <70% [G6]), Tier 3 (credit committee, high exposure/D&B alert/policy exception) — map triggers for each tier per task type

- [ ] Create runtime skill `assets/bayer-credit-analyst-agent/app/skills/guardrails/SKILL.md`:
  - Frontmatter: `name: guardrails`, `description: Eight operational guardrails enforced across all task types.`
  - Body: Define G1–G8 rules in machine-readable format with trigger conditions, blocking behavior, and required log output per guardrail violation

---

## Project-Specific Tasks

## System Prompt & Agent Identity

- [ ] Set agent identity in `assets/bayer-credit-analyst-agent/app/agent.py` system prompt:
  - Role: Bayer Credit Analyst Agent — preventive, forward-looking credit decision support
  - Scope: Bill-to-Cash / Credit Management, Bayer context
  - Mode: Read-Only; no write-back to any system under any circumstances
  - Supported task types: T1 (credit block explanation), T2 (TRM utilization), T3 (DCD decision support), T4 (payment term validation), T5 (seasonal financing eligibility)
  - Escalation: always apply three-tier escalation model; load escalation-model skill for routing decisions
  - Guardrails: always enforce all 8 guardrails; load guardrails skill at every response
  - Confidence: if confidence < 70% on any recommendation, flag for Tier 2 escalation (G6)
  - Data completeness: if any required API call fails, return partial-data warning and escalate to Tier 2
  - All recommendations must cite at least one specific S/4HANA data field as evidence (G8)
  - Never generate numbers, scores, or ratings not derived from tool responses

## MCP Tool Implementation

- [ ] Implement the following MCP tools in `agent.py` (all read-only):

  **Credit Management tools:**
  - `get_credit_management_account(business_partner, credit_segment)` — reads `CreditManagementAccount` entity set from `API_CRDTMBUSINESSPARTNER` (credit limit, utilization, block status, block reason, resubmission date)
  - `get_credit_management_business_partner(business_partner)` — reads `CreditMgmtBusinessPartner` entity set (risk class, score, credit check rule, customer relationship start year)
  - `get_credit_account_collateral(business_partner, credit_segment)` — reads `CrdtMAcctCollateral` and `CrdtMAcctCrdtInsurance` for TRM exposure components
  - `get_bp_negative_events(business_partner)` — reads `CrdtMgmtBPNegativeEvent` entity set

  **Sales credit block tools:**
  - `get_blocked_sales_documents(sold_to_party)` — reads `A_CreditBlockedSalesDocument` entity set from `API_SLS_DOC_WITH_CREDIT_BLOCK` filtered by sold-to party (note: use read-only; do NOT invoke `ReleaseCreditBlock` or `RejectCreditBlock` function imports — G1 enforced)
  - `get_blocked_sales_document_by_id(sales_document)` — reads single blocked document by key

  **Business partner tools:**
  - `get_business_partner_risk_profile(business_partner)` — reads `A_BusinessPartner` + `A_BPCreditWorthiness` from `API_BUSINESS_PARTNER`
  - `get_business_partner_payment_terms(customer, company_code)` — reads `A_CustomerCompany` (PaymentTerms field) from `API_BUSINESS_PARTNER`
  - `get_customer_sales_area_payment_terms(customer, sales_org, dist_channel, division)` — reads `A_CustomerSalesArea` (CustomerPaymentTerms field)

  **Creditworthiness / D&B tool:**
  - `get_creditworthiness(business_partner)` — calls `CREDITWORTHINESSQUERY_IN` SOAP API; validates response data age (guard G5)

- [ ] Wire all tools via `get_mcp_tools()` indirection layer per `guidelines-agent-python.md` — NEVER import directly from `sap_cloud_sdk.agentgateway`

## API Discovery Results File

- [ ] Write `specification/api-discovery-results.md` documenting the discovered APIs:
  - `API_CRDTMBUSINESSPARTNER` | ORD: `sap.s4:apiResource:API_CRDTMBUSINESSPARTNER:v1` | spec: `api-specs/credit-management-business-partner.edmx`
  - `API_SLS_DOC_WITH_CREDIT_BLOCK` | ORD: `sap.s4:apiResource:API_SLS_DOC_WITH_CREDIT_BLOCK:v1` | spec: `api-specs/sales-document-credit-block.edmx`
  - `API_BUSINESS_PARTNER` | ORD: `sap.s4:apiResource:API_BUSINESS_PARTNER:v1` | spec: `api-specs/business-partner.edmx`
  - `CREDITWORTHINESSQUERY_IN` | ORD: `sap.s4:apiResource:CREDITWORTHINESSQUERY_IN:v1` | spec: SOAP (no EDMX, use OpenAPI JSON)
  - `API_DEL_DOC_WITH_CREDIT_BLOCK` | ORD: `sap.s4:apiResource:API_DEL_DOC_WITH_CREDIT_BLOCK:v1` (delivery credit blocks)
  - `OP_DOCUMENTEDCREDITDECISIONERPBUS` | ORD: `sap.s4:apiResource:OP_DOCUMENTEDCREDITDECISIONERPBUS:v1` (DCD — read only)

## MCP Translation File Generation

- [ ] Invoke `mcp-translation-file` skill for each API spec in `api-specs/` to generate MCP translation artifacts
- [ ] After MCP translation, invoke `setup-solution` skill to register generated MCP assets in `solution.yaml` and create `asset.yaml` files
- [ ] Add `requires` entries to `asset.yaml` for each MCP server ORD ID generated

## Task Type Router

- [ ] Implement task type routing in `agent_executor.py` or within `agent.py`:
  - Parse incoming user request to identify task type (T1–T5)
  - Load appropriate runtime skill for the identified task type
  - Load `escalation-model` and `guardrails` skills for every request
  - Return structured response including: task type, recommendation, evidence fields, confidence score, escalation tier, guardrail checks performed

## Guardrail Enforcement

- [ ] Implement guardrail enforcement as a pre/post-processing layer:
  - G1: Block any attempt to call write/update/delete operations — raise guardrail violation immediately
  - G2: Check credit limit headroom before T1/T2 recommendations; flag if recommendation would exceed segment limit
  - G3: Validate DCD instrument type against configurable approved instrument list (T3)
  - G4: Check overdue balance against configurable threshold before seasonal financing eligibility (T5)
  - G5: Validate D&B data age; flag as data-incomplete if >90 days (T5)
  - G6: Calculate confidence score; route to Tier 2 if < 70% on any recommendation
  - G7: Ensure no cross-customer data leakage in tool response aggregation
  - G8: Verify every recommendation output contains at least one explicit S/4HANA field reference
- [ ] Log every guardrail evaluation with: rule ID, trigger condition, data values, pass/fail result

## Escalation Output

- [ ] Implement escalation output formatter:
  - Tier 1: return recommendation with confidence score and evidence
  - Tier 2: return recommendation flagged for Credit Manager review, with escalation reason
  - Tier 3: return recommendation flagged for Credit Committee, with full evidence bundle

---

## Business Instrumentation

- [ ] Implement business step instrumentation for all 5 milestones from the PRD:
  - `M1.achieved: S/4HANA data access verified across all 10 sources for agent initialization`
  - `M1.missed: One or more S/4HANA API connections failed during initialization`
  - `M2.achieved: T1 credit block explanation validated on test case set`
  - `M2.missed: T1 explanation accuracy below threshold or guardrail violation detected`
  - `M3.achieved: T2, T3, T4 task types validated and escalation model confirmed`
  - `M3.missed: One or more of T2/T3/T4 failed validation or escalation trigger test`
  - `M4.achieved: T5 seasonal financing eligibility active with D&B integration verified`
  - `M4.missed: T5 D&B integration failed or G5 guardrail did not trigger on stale data`
  - `M5.achieved: Full escalation model and all 8 guardrails validated in production`
  - `M5.missed: Escalation tier mismatch or guardrail violation detected in production validation`
- [ ] Add OpenTelemetry spans for each milestone and each guardrail evaluation
- [ ] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [ ] Verify `api-discovery-results.md` exists at workspace root with ORD IDs for all required APIs
- [ ] Invoke `mcp-translation-file` skill for API specs in `specification/bayer-credit-analyst-agent/api-specs/`, then invoke `setup-solution` to create/register MCP assets
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` — NEVER import directly from `sap_cloud_sdk.agentgateway`
- [ ] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per MCP server, using exact ORD IDs from generated assets
- [ ] Add the following 4 external MCP server entries to `asset.yaml` under `requires` (Path B — external servers, URL-registered):
  ```yaml
  - name: ical-mcp-server
    kind: mcp-server
    url: https://prod-ical-mcpserver.c-86fbf98.kyma.ondemand.com/mcp
  - name: ekx-mcp-server
    kind: mcp-server
    url: https://prod-ekxmcp-serving.c-86fbf98.kyma.ondemand.com/mcp
  - name: joule-hub-mcp-server
    kind: mcp-server
    url: https://hub.joule.only.sap/mcp
  - name: ask-services-mcp-server
    kind: mcp-server
    url: https://ask-services-rest-api-r2.cfapps.eu10-004.hana.ondemand.com/mcp-server/mcp
  ```
  Note: If the platform requires ORD IDs for these servers, check their `/.well-known/agent.json` or contact the server owners to obtain registered ORD IDs. For now, include `url` fields as the primary reference.
- [ ] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation is complete

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [ ] `conftest.py` only sets `IBD_TESTING=true`
- [ ] Write unit tests in `assets/bayer-credit-analyst-agent/tests/` — one per tool:
  - `test_get_credit_management_account.py`
  - `test_get_credit_management_business_partner.py`
  - `test_get_credit_account_collateral.py`
  - `test_get_bp_negative_events.py`
  - `test_get_blocked_sales_documents.py`
  - `test_get_blocked_sales_document_by_id.py`
  - `test_get_business_partner_risk_profile.py`
  - `test_get_business_partner_payment_terms.py`
  - `test_get_customer_sales_area_payment_terms.py`
  - `test_get_creditworthiness.py`
- [ ] Write integration tests for each task type (T1–T5) end-to-end with mocked responses
- [ ] Write integration test for escalation model (verify tier routing for each trigger condition)
- [ ] Write integration test for guardrail enforcement (verify each G1–G8 triggers correctly)
- [ ] Run `pytest` from `assets/bayer-credit-analyst-agent/` — if coverage < 70%, add tests until threshold met
- [ ] Verify `assets/bayer-credit-analyst-agent/app/agent.py` has exactly 9 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/bayer-credit-analyst-agent/app/agent.py` and confirm returns 9
- [ ] Run `pytest` again to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/bayer-credit-analyst-agent/`
