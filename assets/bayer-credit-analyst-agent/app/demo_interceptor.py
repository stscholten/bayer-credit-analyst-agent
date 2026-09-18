"""
Demo Interceptor — fängt erkannte Demo-Fragen ab und gibt sofort die
Simulation Engine-Antwort zurück, OHNE den LLM aufzurufen.

Aktivierung: Umgebungsvariable DEMO_MODE=1 oder IBD_TESTING=1
"""
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Pfad zur Simulation Engine ─────────────────────────────────────────────
_DEMO_DIR = Path(__file__).parent.parent / "demo"
if str(_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(_DEMO_DIR))

# ── Lazy-Import der Simulation Engine ──────────────────────────────────────
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        try:
            import simulation_engine as se
            _engine = se
            logger.info("Demo Interceptor: Simulation Engine geladen.")
        except Exception as e:
            logger.warning("Demo Interceptor: Simulation Engine nicht verfügbar: %s", e)
    return _engine


# ── Keyword-Mapping: Keywords → Simulation-Funktion ───────────────────────
_RULES = [
    {
        "keywords": ["gesperrt", "kreditblock", "block", "sperr", "2000002", "agro solutions", "blocked"],
        "label": "T1 Kreditblock BP 2000002",
        "fn": lambda se: se.t1_credit_block_explanation(bp="2000002"),
    },
    {
        "keywords": ["auslastung 1000001", "sicherheiten 1000001", "trm 1000001", "treasury 1000001",
                     "kreditlimit-auslastung von bp 1000001", "auslastung von bp 1000001"],
        "fn": lambda se: se.t2_trm_utilization(bp="1000001"),
        "label": "T2 TRM BP 1000001",
    },
    {
        "keywords": ["2000002 auslastung", "auslastung 2000002", "trm 2000002", "risikoampel 2000002",
                     "trm-bewertung"],
        "fn": lambda se: se.t2_trm_utilization(bp="2000002"),
        "label": "T2 TRM BP 2000002",
    },
    {
        "keywords": ["akkreditiv", "letter of credit", " lc ", "lc hinterlegen", "zulässig",
                     "dcd 1000001", "irrevocable"],
        "fn": lambda se: se.t3_dcd_decision_support(bp="1000001", instrument="irrevocable letter of credit"),
        "label": "T3 DCD Akkreditiv",
    },
    {
        "keywords": ["personal cheque", "cheque", "scheck", "personal check", "dcd instrument"],
        "fn": lambda se: se.t3_dcd_decision_support(bp="1000001", instrument="personal cheque"),
        "label": "T3 DCD Personal Cheque",
    },
    {
        "keywords": ["zahlungsbedingungen cu10000001", "cu10000001 konform", "payment term cu10000001",
                     "zahlungsbedingungen hat kunde cu10000001", "zahlungsziel cu10000001"],
        "fn": lambda se: se.t4_payment_term_validation(customer="CU10000001", bp="1000001"),
        "label": "T4 Payment Terms Compliant",
    },
    {
        "keywords": ["60 tage", "risikoklasse 04", "kritisch 60", "60-tage", "policy-konform 60"],
        "fn": lambda se: se.t4_payment_term_mismatch(customer="CU10000001"),
        "label": "T4 Payment Terms Mismatch",
    },
    {
        "keywords": ["saisonale finanzierung 1000001", "saisonal 1000001", "frühjahrs", "eligible 1000001",
                     "geeignet 1000001", "finanzierungsprogramm 2025"],
        "fn": lambda se: se.t5_seasonal_financing(bp="1000001"),
        "label": "T5 Seasonal Eligible",
    },
    {
        "keywords": ["saisonale finanzierung 2000002", "saisonal 2000002", "2000002 finanzierung",
                     "finanzierung 2000002", "not eligible 2000002"],
        "fn": lambda se: se.t5_seasonal_financing(bp="2000002"),
        "label": "T5 Seasonal Not Eligible",
    },
    {
        "keywords": ["eskalationsmodell", "guardrail", "tier 1", "tier 2", "tier 3", "dreistufig",
                     "g1", "g8", "alle guardrails", "acht guardrail"],
        "fn": lambda se: se.demo_escalation_model(),
        "label": "Eskalationsmodell & Guardrails",
    },
]

# Generische Keyword-Fallbacks (einzelne starke Begriffe)
_GENERIC_RULES = [
    {
        "keywords": ["kreditblock", "credit block", "blocked sales"],
        "fn": lambda se: se.t1_credit_block_explanation(bp="2000002"),
        "label": "T1 Kreditblock (generisch)",
    },
    {
        "keywords": ["trm utilization", "trm auslastung", "credit limit utilization"],
        "fn": lambda se: se.t2_trm_utilization(bp="1000001"),
        "label": "T2 TRM (generisch)",
    },
    {
        "keywords": ["dcd", "documentary credit", "letter of credit", "bankgarantie"],
        "fn": lambda se: se.t3_dcd_decision_support(bp="1000001", instrument="irrevocable letter of credit"),
        "label": "T3 DCD (generisch)",
    },
    {
        "keywords": ["zahlungsbedingungen", "payment terms", "zahlungsziel"],
        "fn": lambda se: se.t4_payment_term_validation(customer="CU10000001", bp="1000001"),
        "label": "T4 Payment Terms (generisch)",
    },
    {
        "keywords": ["saisonale", "seasonal financing", "frühjahr"],
        "fn": lambda se: se.t5_seasonal_financing(bp="1000001"),
        "label": "T5 Seasonal (generisch)",
    },
]


def is_demo_mode() -> bool:
    """Gibt True zurück wenn DEMO_MODE=1 oder IBD_TESTING=1 gesetzt ist."""
    return (
        os.environ.get("DEMO_MODE", "").strip() in ("1", "true", "yes") or
        os.environ.get("IBD_TESTING", "").strip() in ("1", "true", "yes")
    )


def intercept(query: str) -> str | None:
    """
    Prüft ob die Anfrage eine bekannte Demo-Frage ist.

    Returns:
        Simulierte Antwort als String, oder None wenn kein Match.
    """
    if not is_demo_mode():
        return None

    se = _get_engine()
    if se is None:
        return None

    q = query.lower().strip()

    # Zuerst: spezifische Regeln (höhere Präzision)
    for rule in _RULES:
        score = sum(1 for kw in rule["keywords"] if kw in q)
        if score >= 1:
            try:
                result = rule["fn"](se)
                logger.info("Demo Interceptor: '%s' erkannt → %s", query[:60], rule["label"])
                return _wrap_demo_response(result, rule["label"])
            except Exception as e:
                logger.warning("Demo Interceptor Fehler bei '%s': %s", rule["label"], e)
                return None

    # Dann: generische Fallbacks
    for rule in _GENERIC_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in q)
        if score >= 1:
            try:
                result = rule["fn"](se)
                logger.info("Demo Interceptor (generisch): '%s' → %s", query[:60], rule["label"])
                return _wrap_demo_response(result, rule["label"])
            except Exception as e:
                logger.warning("Demo Interceptor Fehler (generisch) bei '%s': %s", rule["label"], e)
                return None

    logger.debug("Demo Interceptor: kein Match für '%s'", query[:60])
    return None


def _wrap_demo_response(raw: str, label: str) -> str:
    """Verpackt die Simulation Engine-Antwort in einen Demo-Hinweis."""
    note = (
        "📋 **[DEMO-MODUS — Simulierte Antwort]**\n"
        f"_Aufgabe: {label}_\n\n"
    )
    # Einfacher Text-Block ohne Markdown-Box (funktioniert in jedem Client)
    return note + raw
