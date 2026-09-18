"""
Credit Analyst Agent — MCP Tool Wrappers

All SAP API interactions go through MCP tools via get_mcp_tools().
NEVER call SAP APIs directly — no requests, httpx, or direct OData clients.
"""
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def check_dandb_data_age(standing_date_str: str | None, max_age_days: int = 90) -> dict:
    """Guardrail G5: Validate D&B data age. Returns dict with is_stale and age_days."""
    if not standing_date_str:
        return {"is_stale": True, "age_days": None, "reason": "D&B date not available"}
    try:
        # Handle both ISO date strings and /Date(ms)/ format
        if standing_date_str.startswith("/Date("):
            ms = int(standing_date_str[6:-2])
            standing_date = datetime.fromtimestamp(ms / 1000)
        else:
            standing_date = datetime.fromisoformat(standing_date_str[:10])
        age_days = (datetime.now() - standing_date).days
        is_stale = age_days > max_age_days
        return {"is_stale": is_stale, "age_days": age_days, "standing_date": standing_date_str}
    except Exception as exc:
        logger.warning("Failed to parse D&B standing date '%s': %s", standing_date_str, exc)
        return {"is_stale": True, "age_days": None, "reason": f"Date parse error: {exc}"}


def calculate_utilization_pct(
    credit_limit: float | None,
    net_exposure: float | None
) -> float | None:
    """Calculate credit utilization percentage safely."""
    if not credit_limit or credit_limit == 0:
        return None
    if net_exposure is None:
        return None
    return round((net_exposure / credit_limit) * 100, 2)


def get_utilization_tier(utilization_pct: float | None) -> str:
    """Map utilization % to GREEN/AMBER/RED tier."""
    if utilization_pct is None:
        return "UNKNOWN"
    if utilization_pct <= 70:
        return "GREEN"
    if utilization_pct <= 90:
        return "AMBER"
    return "RED"


def calculate_eligibility_score(
    risk_class: str | None,
    dandb_rating: str | None,
    has_overdue_block: bool,
    negative_event_count: int,
) -> int:
    """Calculate seasonal financing eligibility score (0-100)."""
    score = 0

    # Risk class contribution
    risk_points = {"01": 40, "02": 25, "03": 10, "04": -20}
    score += risk_points.get(risk_class or "", 0)

    # D&B rating contribution
    if dandb_rating:
        r = dandb_rating.upper()
        if r in ("AAA", "AA", "A"):
            score += 30
        elif r in ("BBB", "BB", "B"):
            score += 15
        elif r:
            score -= 20

    # Overdue block
    if has_overdue_block:
        score -= 30
    else:
        score += 20

    # Negative events
    if negative_event_count == 0:
        score += 10
    else:
        score -= 20 * min(negative_event_count, 2)

    return max(0, min(100, score))


def get_eligibility_decision(score: int) -> str:
    """Map eligibility score to decision."""
    if score >= 70:
        return "ELIGIBLE"
    if score >= 50:
        return "CONDITIONAL"
    return "NOT ELIGIBLE"


BLOCK_REASON_DESCRIPTIONS = {
    "01": "Credit limit exceeded — outstanding receivables exceed the approved credit limit",
    "02": "Credit limit validity expired — the credit limit has passed its valid-to date",
    "03": "Critical customer flag — customer is marked for special attention",
    "04": "Risk class block — customer's risk class requires manual credit approval",
    "05": "Negative event recorded — a negative credit event is on record",
    "06": "Missing credit information — mandatory credit data is incomplete",
    "07": "Manual block — credit analyst has placed a manual hold on the account",
    "08": "Financial document check failed — required documentary credit instrument is missing or expired",
    "09": "Overdue items — customer has open items past due date exceeding tolerance",
    "10": "New customer — first-order block pending initial credit assessment",
}


def get_block_reason_description(code: str | None) -> str:
    """Return plain-language description for a credit block reason code."""
    if not code:
        return "Unknown block reason"
    return BLOCK_REASON_DESCRIPTIONS.get(
        code.strip(),
        f"Credit block (reason code {code} — refer to SAP Credit Management configuration)"
    )


APPROVED_DCD_INSTRUMENTS = {
    "irrevocable_lc", "irrevocable letter of credit",
    "confirmed_lc", "confirmed letter of credit",
    "bank_guarantee", "bank guarantee",
    "standby_lc", "standby letter of credit",
    "documentary_collection", "documentary collection", "d/a", "d/p",
    "advance_payment", "advance payment",
}


def is_approved_dcd_instrument(instrument_type: str | None) -> bool:
    """G3: Check if a DCD instrument type is on the approved list."""
    if not instrument_type:
        return False
    return instrument_type.lower().strip() in APPROVED_DCD_INSTRUMENTS


RISK_CLASS_PAYMENT_TERM_LIMITS = {
    "01": {"max_days": 90, "label": "Net 90 or better"},
    "02": {"max_days": 45, "label": "Net 45 or better"},
    "03": {"max_days": 30, "label": "Net 30 or better"},
    "04": {"max_days": 0, "label": "Advance payment only"},
}


def validate_payment_terms(payment_term_days: int | None, risk_class: str | None) -> dict:
    """T4: Validate payment terms against risk class tolerance matrix."""
    if payment_term_days is None:
        return {"result": "UNKNOWN", "reason": "Payment term days not determinable"}
    if risk_class is None:
        return {"result": "UNKNOWN", "reason": "Risk class not available"}

    limits = RISK_CLASS_PAYMENT_TERM_LIMITS.get(risk_class, {"max_days": 60, "label": "Net 60"})
    max_days = limits["max_days"]

    if max_days == 0 and payment_term_days > 0:
        return {
            "result": "MISMATCH",
            "reason": f"Risk class {risk_class} requires advance payment only, but credit terms of {payment_term_days} days are agreed",
            "policy": limits["label"],
        }
    if payment_term_days > max_days:
        return {
            "result": "MISMATCH",
            "reason": f"Agreed terms of {payment_term_days} days exceed limit of {max_days} days for risk class {risk_class}",
            "policy": limits["label"],
        }
    if payment_term_days >= max_days * 0.9:
        return {
            "result": "BORDERLINE",
            "reason": f"Agreed terms of {payment_term_days} days are at the limit for risk class {risk_class}",
            "policy": limits["label"],
        }
    return {
        "result": "COMPLIANT",
        "reason": f"Agreed terms of {payment_term_days} days are within policy for risk class {risk_class}",
        "policy": limits["label"],
    }
