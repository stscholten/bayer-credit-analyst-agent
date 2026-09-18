# Product Requirements Document (PRD)

**Title:** Bayer Credit Analyst Agent  
**Date:** 2026-09-18  
**Owner:** Bayer Finance / Bill-to-Cash Credit Management  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Bayer's Credit Analysts spend ~3.5 hours per credit decision manually correlating data across 10 S/4HANA sources. This agent provides instant, explainable, guardrail-bound recommendations for five credit task types — cutting decision time to under 30 minutes while preserving full analyst control.

**Business Need:**  
Existing SAP standard agents (Collections, Dispute, Clearing, AR) are reactive and focus on invoice-to-cash execution. There is no proactive AI support for credit decisions upstream. Analysts must manually assess credit blocks, TRM limit utilization, documentary credit decisions, payment term plausibility, and seasonal financing eligibility — creating bottlenecks, inconsistent decisions, and elevated credit risk exposure.

**Expected Value:**  
- Average credit decision time reduced from ~3.5 hours to under 30 minutes  
- 50–60% of credit blocks resolved without manual escalation  
- >85% recommendation accuracy (analyst agreement rate, 100-case evaluation basis)  
- DSO improvement as secondary observation metric

**Product Objectives:**
1. Deliver accurate, explainable credit recommendations across all 5 task types within guardrail boundaries
2. Reduce average decision processing time from 3.5 hours to under 30 minutes
3. Enable 50–60% autonomous analysis of credit blocks without escalation

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Average credit decision processing time | ~3.5 hours | < 30 minutes | — | Credit Block Analysis / Payment Term Validation | user |
| Share of credit blocks resolved without manual escalation | 0% | 50–60% | — | T1 Credit Block Explanation / Escalation Model | user |
| Recommendation accuracy (analyst agreement rate) | — | > 85% | Measured over 100-case evaluation basis | All 5 task types | user |
| Days Sales Outstanding (DSO) improvement | — | Observation metric (no fixed target) | — | Preventive credit decision support | user |

---

## Requirements

### Must-Have Requirements

**REQ-01: T1 — Credit Block Explanation**
- **User Story:** As a Credit Analyst, I need a plain-language explanation of why a sales order or customer account is blocked so that I can quickly assess the root cause and decide on the appropriate action.
- **Acceptance Criteria:**
  - Given a blocked sales order or customer, when I request a credit block analysis, then the agent returns the triggered credit rule(s), threshold values, current exposure data, and a human-readable explanation.
  - The explanation references specific S/4HANA credit segment data and business partner risk category.
- **Priority Rank:** 1

**REQ-02: T2 — TRM Credit Limit Utilization**
- **User Story:** As a Credit Analyst, I need an assessment of a customer's credit limit utilization including Treasury/Risk Management data so that I can evaluate actual vs. available credit exposure.
- **Acceptance Criteria:**
  - Given a customer credit account, when I request TRM utilization, then the agent returns current utilization %, available headroom, TRM-specific exposure components, and a risk-tiered interpretation.
- **Priority Rank:** 2

**REQ-03: T3 — DCD Documentary Credit Decision Support**
- **User Story:** As a Credit Analyst, I need decision support for Documentary Credit Decisions (letters of credit, bank guarantees) so that I can assess instrument adequacy against customer risk profile.
- **Acceptance Criteria:**
  - Given a customer and transaction context, when I request DCD support, then the agent returns a structured recommendation on instrument type, coverage adequacy, and risk factors with supporting data.
- **Priority Rank:** 3

**REQ-04: T4 — Payment Term Validation**
- **User Story:** As a Credit Analyst, I need validation of agreed payment terms against the customer's risk profile so that I can identify misalignments before they create collection risk.
- **Acceptance Criteria:**
  - Given a customer's agreed payment terms and risk profile data, when I request validation, then the agent identifies plausibility gaps, flags exceptions, and provides a recommendation with evidence.
- **Priority Rank:** 4

**REQ-05: T5 — Seasonal Financing Eligibility**
- **User Story:** As a Credit Analyst, I need an eligibility assessment for seasonal financing models so that I can proactively offer or restrict seasonal payment structures based on objective criteria.
- **Acceptance Criteria:**
  - Given a customer's financial history, payment behaviour, and D&B creditworthiness data, when I request seasonal financing eligibility, then the agent returns an eligibility score, key determining factors, and a recommendation.
- **Priority Rank:** 5

**REQ-06: Read-Only Enforcement**
- **User Story:** As a Credit Manager, I need the agent to operate strictly in read-only mode so that no automated write-backs occur in S/4HANA.
- **Acceptance Criteria:**
  - The agent MUST NOT execute any write, update, or create operations on any S/4HANA entity or external system.
  - All data retrieval is via read-only API calls. Any attempt to invoke a write operation is blocked by a guardrail and logged.
- **Priority Rank:** 1

**REQ-07: Three-Tier Escalation Model**
- **User Story:** As a Credit Analyst, I need the agent to escalate to the appropriate human authority when a case exceeds defined thresholds so that I am not presented with unsupported recommendations for high-risk decisions.
- **Acceptance Criteria:**
  - Tier 1 (Analyst): Agent provides recommendation, no escalation needed. Standard confidence and risk thresholds met.
  - Tier 2 (Credit Manager): Agent flags case for manager review. Triggered by moderate risk signals, conflicting data, or borderline thresholds.
  - Tier 3 (Credit Committee): Agent recommends committee escalation. Triggered by high exposure, external credit events (D&B alerts), or policy exceptions.
- **Priority Rank:** 2

**REQ-08: Eight Guardrails**
- **User Story:** As a Credit Manager, I need the agent to operate within eight defined guardrails so that all recommendations stay within Bayer's credit policy boundaries.
- **Acceptance Criteria:**
  - G1: No write-back to any system (Read-Only).
  - G2: No recommendations exceeding the customer's assigned credit segment limit without escalation flag.
  - G3: No DCD recommendations for instruments not on the approved instrument list.
  - G4: No seasonal financing eligibility approval for customers with overdue balance > X days (configurable).
  - G5: D&B data must be available and < 90 days old for T5 recommendations; otherwise flag as data-incomplete.
  - G6: Confidence below 70% on any recommendation must trigger Tier 2 escalation.
  - G7: No cross-customer data disclosure in multi-tenant or multi-account queries.
  - G8: All recommendations must be traceable to at least one S/4HANA data field; no LLM-only conclusions.
- **Priority Rank:** 1

---

## Solution Architecture

**Architecture Overview:**  
Python AI Agent (A2A protocol) deployed on SAP BTP. The agent integrates with SAP S/4HANA via OData/SOAP APIs and with D&B via the SAP Credit Integration Service. No MCP servers are currently available for the relevant APIs; direct API integration is used.

**Key Components:**
- Python AI Agent (A2A): core reasoning engine, task routing, guardrail enforcement, escalation logic
- S/4HANA API Layer: 10 data sources accessed read-only (credit management, business partner, receivables, payment terms, TRM)
- D&B Creditworthiness Integration: via `CREDITWORTHINESSQUERY_IN` SOAP API / SAP Credit Integration Service
- Escalation Notification: output channel for Tier 2/3 escalation alerts (email or SAP Fiori notification)

**Integration Points:**
- `OP_API_CRDTMBUSINESSPARTNER_0001` — Credit management master data (read)
- `CREDITMANAGEMENTACCOUNTBYIDQU1` — Credit account by ID (read)
- `API_BUSINESS_PARTNER` — Business partner risk profile, payment terms (read)
- `CREDITWORTHINESSQUERY_IN` — External D&B creditworthiness data (read)
- `API_CRDTMBUSINESSPARTNER` — Credit management business partner master (read)

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- Task type handlers (T1–T5) are implemented as isolated, pluggable skill modules — new task types can be added without modifying core agent logic.
- Guardrail rules are configuration-driven (not hardcoded) to allow policy updates without redeployment.
- Escalation thresholds and tier definitions are externalized as configurable parameters.

**Business Step Instrumentation:**
- All 5 task type executions emit structured log statements at entry, completion, and escalation trigger points.
- Guardrail evaluations are logged with the specific rule triggered and the data values that caused the trigger.
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- Instrumentation supports OpenTelemetry spans for end-to-end traceability of each credit decision session.

### Automation & Agent Behaviour

**Automation Level:** ML-assisted / Autonomous agent (Read-Only, recommendation-only)

**Actions performed without human approval:**
- Data retrieval from all integrated S/4HANA APIs
- Credit rule evaluation and threshold comparison
- Risk scoring and utilization calculation
- Recommendation generation (all 5 task types)
- Escalation tier determination

**Actions requiring human review or approval:**
- All final credit decisions (the agent recommends; the analyst decides)
- Tier 2 and Tier 3 escalations require human action
- Any action resulting in a change to S/4HANA data (explicitly out of scope / blocked)

**Model:** SAP Generative AI Hub (LLM for reasoning and explanation generation)

**Knowledge & data sources accessed:**
- SAP S/4HANA Credit Management: credit limits, segments, blocks, exposure
- SAP S/4HANA Business Partner: risk category, payment terms, customer master
- SAP S/4HANA Receivables: open items, aging, overdue analysis
- SAP S/4HANA TRM: treasury risk data, financial instruments exposure
- D&B Creditworthiness: external credit score, financial alerts, company data

**Guardrails & fail-safes:**
- G1–G8 as defined in REQ-08 above
- If any S/4HANA API call fails, the agent returns a partial-data warning and escalates to Tier 2
- If D&B data is unavailable for T5, the agent flags as data-incomplete and does not return an eligibility recommendation
- Confidence scoring on all recommendations; below-threshold results trigger automatic Tier 2 escalation

---

## Milestones

### M1: S/4HANA Data Access Established

- **Description:** Agent successfully retrieves data from all 10 S/4HANA data sources via read-only API calls.
- **Achieved when:** All API integrations return valid data for a test business partner in the development environment.
- **Log on achievement:** `M1.achieved: S/4HANA data access verified across all 10 sources for agent initialization`
- **Log on miss:** `M1.missed: One or more S/4HANA API connections failed during initialization`

### M2: T1 Credit Block Explanation Operational

- **Description:** Agent produces guardrail-compliant, explainable credit block analysis for blocked orders and customers.
- **Achieved when:** T1 task type returns correct rule attribution, exposure data, and human-readable explanation for 10 test cases with >85% analyst agreement.
- **Log on achievement:** `M2.achieved: T1 credit block explanation validated on test case set`
- **Log on miss:** `M2.missed: T1 explanation accuracy below threshold or guardrail violation detected`

### M3: T2–T4 Task Types Validated

- **Description:** TRM utilization scoring (T2), DCD decision support (T3), and payment term validation (T4) are live and tested.
- **Achieved when:** All three task types return recommendations within guardrail boundaries for defined test cases; escalation logic triggers correctly.
- **Log on achievement:** `M3.achieved: T2, T3, T4 task types validated and escalation model confirmed`
- **Log on miss:** `M3.missed: One or more of T2/T3/T4 failed validation or escalation trigger test`

### M4: T5 Seasonal Financing Eligibility with D&B Active

- **Description:** Agent assesses seasonal financing eligibility combining S/4HANA data with D&B external creditworthiness.
- **Achieved when:** T5 returns eligibility recommendation with D&B data integrated; data-age guardrail (G5) triggers correctly for outdated D&B records.
- **Log on achievement:** `M4.achieved: T5 seasonal financing eligibility active with D&B integration verified`
- **Log on miss:** `M4.missed: T5 D&B integration failed or G5 guardrail did not trigger on stale data`

### M5: Escalation Model and All Guardrails in Production

- **Description:** Three-tier escalation model and all 8 guardrails operate correctly across all task types in production.
- **Achieved when:** Escalation tier routing is verified for 15+ test scenarios; all 8 guardrails are validated end-to-end; no write-back incidents recorded.
- **Log on achievement:** `M5.achieved: Full escalation model and all 8 guardrails validated in production`
- **Log on miss:** `M5.missed: Escalation tier mismatch or guardrail violation detected in production validation`
