# API Discovery Results — Bayer Credit Analyst Agent

Discovered APIs relevant to the Bill-to-Cash Credit Management use case.

## S/4HANA Credit Management APIs

| API Name | Type | ORD ID | Spec File | Usage |
|----------|------|--------|-----------|-------|
| Credit Management Master Data | OData | `sap.s4:apiResource:API_CRDTMBUSINESSPARTNER:v1` | `api-specs/credit-management-business-partner.edmx` | T1, T2, T3, T4, T5 — credit limits, utilization, block status, collateral |
| Sales Document with Credit Block | OData | `sap.s4:apiResource:API_SLS_DOC_WITH_CREDIT_BLOCK:v1` | `api-specs/sales-document-credit-block.edmx` | T1 — blocked sales orders (read-only) |
| Business Partner A2X | OData | `sap.s4:apiResource:API_BUSINESS_PARTNER:v1` | `api-specs/business-partner.edmx` | T4 — risk profile, payment terms, creditworthiness |
| Delivery Document with Credit Block | OData | `sap.s4:apiResource:API_DEL_DOC_WITH_CREDIT_BLOCK:v1` | — | T1 — blocked delivery documents |
| Documented Credit Decision | SOAP | `sap.s4:apiResource:OP_DOCUMENTEDCREDITDECISIONERPBUS:v1` | — | T3 — DCD read operations |

## External Creditworthiness

| API Name | Type | ORD ID | Usage |
|----------|------|--------|-------|
| Credit Worthiness Information – Read | SOAP | `sap.s4:apiResource:CREDITWORTHINESSQUERY_IN:v1` | T5 — D&B creditworthiness data with data-age validation (G5) |

## MCP Server Status

No pre-existing MCP servers found for the above APIs. MCP translation files must be generated from the downloaded EDMX specs using the `mcp-translation-file` skill.
