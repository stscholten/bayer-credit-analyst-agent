"""
Mock MCP Client — liefert Testdaten aus mcp-mock.json.
Ersetzt echte MCP-Aufrufe vollständig im Demo-Modus.
"""
import json
import os

_MOCK_PATH = os.path.join(os.path.dirname(__file__), "..", "mcp-mock.json")

with open(_MOCK_PATH, encoding="utf-8") as f:
    _MOCK = json.load(f)

_SERVERS = _MOCK["servers"]


def _tool(server: str, tool: str) -> dict:
    return _SERVERS[server]["tools"][tool]["mock_response"]


def get_credit_account(bp: str) -> dict:
    if bp == "2000002":
        return _tool("s4-credit-management", "get_credit_management_account_blocked")
    return _tool("s4-credit-management", "get_credit_management_account")


def get_bp_risk_profile(bp: str) -> dict:
    base = _tool("s4-credit-management", "get_credit_management_business_partner")
    if bp == "2000002":
        return {**base, "BusinessPartner": "2000002", "CreditRiskClass": "04",
                "CreditWorthinessScoreValue": "180"}
    return base


def get_creditworthiness(bp: str) -> dict:
    base = _tool("s4-creditworthiness", "get_creditworthiness")
    if bp == "2000002":
        return {**base, "BusinessPartner": "2000002",
                "BPCreditStandingRating": "CCC",
                "BPCreditStandingComment": "High default risk — multiple overdue items",
                "BPCreditStandingDate": "/Date(1706745600000)/"}
    return base


def get_payment_terms(customer: str) -> dict:
    return _tool("s4-business-partner", "get_business_partner_payment_terms")


def get_collateral(bp: str) -> dict:
    return _tool("s4-credit-management", "get_credit_account_collateral")


def get_negative_events(bp: str) -> list:
    if bp == "2000002":
        return [
            {"EventType": "OVERDUE", "EventDate": "/Date(1717200000000)/", "Description": "3 overdue invoices"},
            {"EventType": "DISPUTE", "EventDate": "/Date(1720137600000)/", "Description": "Open dispute case"},
        ]
    return _tool("s4-credit-management", "get_bp_negative_events").get("results", [])


def get_all_blocked_documents(bp: str) -> list:
    if bp == "2000002":
        return _tool("s4-sales-credit-block", "get_blocked_sales_documents").get("results", [])
    return []
