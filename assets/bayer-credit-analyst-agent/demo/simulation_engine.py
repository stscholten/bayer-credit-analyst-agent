"""
Simulation Engine — erzeugt strukturierte, realistische Agentenantworten ohne LLM-Aufruf.
Alle Antworten basieren ausschließlich auf mcp-mock.json (Read-Only).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from tools import (
    check_dandb_data_age,
    calculate_utilization_pct,
    get_utilization_tier,
    calculate_eligibility_score,
    get_eligibility_decision,
    get_block_reason_description,
    validate_payment_terms,
    is_approved_dcd_instrument,
    RISK_CLASS_PAYMENT_TERM_LIMITS,
)
from mock_mcp_client import (
    get_credit_account,
    get_bp_risk_profile,
    get_creditworthiness,
    get_payment_terms,
    get_collateral,
    get_negative_events,
    get_all_blocked_documents,
)

DIVIDER = "─" * 72
SECTION  = "═" * 72


def _header(title: str, task_type: str) -> str:
    return f"\n{SECTION}\n  🔍 {task_type}  |  {title}\n{SECTION}"


def _footer(tier: str, guardrails: list) -> str:
    g_text = "  ".join(f"✅ {g}" for g in guardrails)
    return f"\n{DIVIDER}\n  Eskalationsstufe: {tier}\n  Guardrails geprüft: {g_text}\n{DIVIDER}"


# ─────────────────────────────────────────────────────────────────────────────
# T1 — Kreditblock-Erklärung
# ─────────────────────────────────────────────────────────────────────────────

def t1_credit_block_explanation(bp: str = "2000002") -> str:
    acct   = get_credit_account(bp)
    risk   = get_bp_risk_profile(bp)
    docs   = get_all_blocked_documents(bp)
    events = get_negative_events(bp)

    block_code  = acct.get("CreditAccountBlockReason", "")
    is_blocked  = acct.get("CreditAccountIsBlocked", False)
    limit       = float(acct.get("CreditLimitAmount", 0))
    calc_limit  = float(acct.get("CreditLimitCalculatedAmount", limit))
    risk_class  = risk.get("CreditRiskClass", "N/A")
    score       = risk.get("CreditWorthinessScoreValue", "N/A")

    utilization  = calculate_utilization_pct(limit, calc_limit)
    tier         = get_utilization_tier(utilization)
    reason_text  = get_block_reason_description(block_code)

    blocked_orders      = len(docs)
    total_blocked_value = sum(float(d.get("TotalNetAmount", 0)) for d in docs)

    lines = [_header(f"Kreditblock-Analyse — Business Partner {bp}", "T1 KREDITBLOCK-ERKLÄRUNG")]
    lines.append(f"""
  KUNDENPROFIL
  ├─ Business Partner:     {bp}
  ├─ Kreditlimit:          {limit:,.2f} EUR
  ├─ Risikoklasse:         {risk_class}
  ├─ Bonitätsscore:        {score}
  └─ Status:               {"⛔ GESPERRT" if is_blocked else "✅ AKTIV"}

  BLOCKIERUNGSURSACHE
  ├─ Code:                 {block_code if block_code else "–"}
  └─ Erklärung:            {reason_text}

  BETROFFENE AUFTRÄGE
  ├─ Anzahl gesperrter Aufträge:     {blocked_orders}
  └─ Gesamtwert gesperrter Aufträge: {total_blocked_value:,.2f} EUR

  KREDITAUSLASTUNG
  ├─ Berechnetes Limit:    {calc_limit:,.2f} EUR
  ├─ Auslastung:           {utilization:.1f}%
  └─ Ampelstatus:          {"🔴 ROT" if tier == "RED" else "🟡 AMBER" if tier == "AMBER" else "🟢 GRÜN"}

  NEGATIVE EREIGNISSE:     {"Keine" if not events else f"{len(events)} Einträge"}

  EMPFEHLUNG
  ├─ Der Kreditblock wurde durch Überschreitung des Kreditlimits ausgelöst.
  ├─ Die Auslastung von {utilization:.1f}% übersteigt das genehmigte Limit.
  ├─ Empfohlen: Überprüfung durch den Credit Manager (Tier 2).
  └─ Mögliche Maßnahmen: Anzahlung, Sicherheitenerhöhung oder Limitanpassung.
""")
    lines.append(_footer(
        "Tier 2 — Credit Manager",
        ["G1 Read-Only", "G2 Limitcheck", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# T2 — TRM Utilization
# ─────────────────────────────────────────────────────────────────────────────

def t2_trm_utilization(bp: str = "1000001") -> str:
    acct      = get_credit_account(bp)
    risk      = get_bp_risk_profile(bp)
    collateral = get_collateral(bp)

    limit     = float(acct.get("CreditLimitAmount", 0))
    calc      = float(acct.get("CreditLimitCalculatedAmount", limit))
    requested = float(acct.get("CreditLimitRequestedAmount", 0))
    currency  = acct.get("CreditSegmentCurrency", "EUR")
    risk_class = risk.get("CreditRiskClass", "N/A")

    utilization = calculate_utilization_pct(limit, calc)
    tier        = get_utilization_tier(utilization)

    collateral_items = collateral.get("results", [])
    collateral_total = sum(float(c.get("AddlCreditDocAmtInTransacCrcy", 0)) for c in collateral_items)
    collateral_desc  = collateral_items[0].get("AdditionalCreditDocComment", "–") if collateral_items else "–"

    tier_icon  = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}.get(tier, "⚪")
    tier_label = {
        "GREEN": "GRÜN — im Normbereich",
        "AMBER": "AMBER — erhöhte Aufmerksamkeit",
        "RED":   "ROT — Eskalation erforderlich",
    }.get(tier, "UNBEKANNT")

    lines = [_header(f"TRM Kreditlimit-Auslastung — Business Partner {bp}", "T2 TRM UTILIZATION")]
    lines.append(f"""
  KREDITLIMIT-ÜBERSICHT
  ├─ Genehmigtes Limit:    {limit:,.2f} {currency}
  ├─ Berechnete Nutzung:   {calc:,.2f} {currency}
  ├─ Beantragt:            {requested:,.2f} {currency}
  ├─ Auslastung:           {utilization:.1f}%
  └─ TRM-Ampelstatus:      {tier_icon}  {tier_label}

  TREASURY / SICHERHEITEN
  ├─ Hinterlegte Sicherheiten: {collateral_total:,.2f} {currency}
  └─ Beschreibung:             {collateral_desc}

  RISIKOKLASSE:  {risk_class}  (Skala 01=sehr gut … 04=kritisch)

  BEWERTUNG
  ├─ Auslastung {utilization:.1f}% liegt {"ÜBER der AMBER-Schwelle von 70%." if utilization > 70 else "im grünen Bereich unter 70%."}
  ├─ Sicherheiten decken {(collateral_total / limit * 100) if limit > 0 else 0:.1f}% des genehmigten Limits ab.
  └─ {"Präventive Limiterhöhung oder Sicherheitenstärkung wird empfohlen." if utilization > 70 else "Keine unmittelbare Maßnahme erforderlich. Monitoring beibehalten."}
""")
    lines.append(_footer(
        "Tier 1 — Analyst" if tier == "GREEN" else "Tier 2 — Credit Manager",
        ["G1 Read-Only", "G2 Limitcheck", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# T3 — DCD Decision Support
# ─────────────────────────────────────────────────────────────────────────────

def t3_dcd_decision_support(bp: str = "1000001", instrument: str = "Bank Guarantee") -> str:
    acct       = get_credit_account(bp)
    risk       = get_bp_risk_profile(bp)
    collateral = get_collateral(bp)
    cw         = get_creditworthiness(bp)

    risk_class = risk.get("CreditRiskClass", "N/A")
    score      = risk.get("CreditWorthinessScoreValue", "N/A")
    limit      = float(acct.get("CreditLimitAmount", 0))
    currency   = acct.get("CreditSegmentCurrency", "EUR")

    is_approved      = is_approved_dcd_instrument(instrument)
    collateral_items = collateral.get("results", [])
    existing_col     = collateral_items[0].get("AdditionalCreditDocComment", "–") if collateral_items else "–"

    cw_rating  = cw.get("BPCreditStandingRating", "N/A")
    cw_comment = cw.get("BPCreditStandingComment", "–")
    is_bankrupt = cw.get("BusinessPartnerIsBankrupt", False)
    has_legal   = cw.get("BPLegalProceedingStatus", "00") != "00"

    instrument_icon = "✅" if is_approved else "⛔"

    lines = [_header(f"DCD Entscheidungsunterstützung — BP {bp} | Instrument: {instrument}", "T3 DCD DECISION SUPPORT")]
    lines.append(f"""
  GESCHÄFTSPARTNER-PROFIL
  ├─ Business Partner:     {bp}
  ├─ Risikoklasse:         {risk_class}
  ├─ Bonitätsscore:        {score}
  ├─ D&B Rating:           {cw_rating}
  └─ D&B Kommentar:        {cw_comment}

  DOKUMENTARISCHES INSTRUMENT
  ├─ Gewünschtes Instrument: {instrument}
  ├─ Zulässigkeit (G3):    {instrument_icon} {"GENEHMIGT — auf der Positivliste" if is_approved else "ABGELEHNT — nicht auf der genehmigten Instrumentenliste"}
  └─ Vorhandene Sicherheit: {existing_col}

  RISIKOPRÜFUNG
  ├─ Insolvenz:            {"⛔ JA — Eskalation Tier 3 erforderlich" if is_bankrupt else "✅ Nein"}
  ├─ Gerichtsverfahren:    {"⛔ JA — Eskalation Tier 3 erforderlich" if has_legal else "✅ Nein"}
  └─ Kreditlimit:          {limit:,.2f} {currency}

  EMPFEHLUNG
  {"├─ ⛔ Instrument nicht genehmigt — Verwendung abgelehnt (Guardrail G3)." if not is_approved else "├─ ✅ Instrument genehmigt. Beantragung kann fortgesetzt werden."}
  ├─ Risikoklasse {risk_class} erfordert {"erhöhte" if risk_class in ("03","04") else "Standard-"}Dokumentationssorgfalt.
  └─ {"Genehmigung durch Credit Committee (Tier 3) erforderlich." if is_bankrupt or has_legal else "Credit Manager (Tier 2) kann Genehmigung erteilen."}
""")
    lines.append(_footer(
        "Tier 3 — Credit Committee" if is_bankrupt or has_legal else "Tier 2 — Credit Manager",
        ["G1 Read-Only", "G3 DCD-Instrument", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# T4 — Payment Term Validation
# ─────────────────────────────────────────────────────────────────────────────

def t4_payment_term_validation(customer: str = "CU10000001", bp: str = "1000001") -> str:
    pt   = get_payment_terms(customer)
    risk = get_bp_risk_profile(bp)

    risk_class        = risk.get("CreditRiskClass", "N/A")
    payment_term_code = pt.get("PaymentTerms", "N/A")
    score             = risk.get("CreditWorthinessScoreValue", "N/A")

    payment_days_map = {
        "ZB30": 30, "ZB45": 45, "ZB60": 60, "ZB90": 90, "ZB14": 14,
        "NT30": 30, "NT45": 45, "NT60": 60, "SOFORT": 0,
    }
    payment_days = payment_days_map.get(payment_term_code, 30)

    validation   = validate_payment_terms(payment_days, risk_class)
    result       = validation["result"]
    reason       = validation["reason"]
    policy       = validation["policy"]
    policy_limit = RISK_CLASS_PAYMENT_TERM_LIMITS.get(risk_class, {})

    result_icon = {"COMPLIANT": "✅", "BORDERLINE": "🟡", "MISMATCH": "⛔", "UNKNOWN": "❓"}.get(result, "❓")

    lines = [_header(f"Zahlungsbedingungen-Validierung — Kunde {customer}", "T4 PAYMENT TERM VALIDATION")]
    lines.append(f"""
  KUNDENPROFIL
  ├─ Kundennummer:         {customer}
  ├─ Risikoklasse:         {risk_class}
  ├─ Bonitätsscore:        {score}
  └─ Policy-Grenze:        {policy_limit.get("label", "N/A")}

  VEREINBARTE ZAHLUNGSBEDINGUNG
  ├─ Zahlungsbedingungscode:  {payment_term_code}
  └─ Zahlungsziel (Tage):     {payment_days} Tage

  VALIDIERUNGSERGEBNIS
  ├─ Status:               {result_icon}  {result}
  ├─ Begründung:           {reason}
  └─ Policy:               {policy}

  EMPFEHLUNG
  {"├─ ✅ Zahlungsbedingung entspricht der Risikopolitik. Keine Maßnahme erforderlich." if result == "COMPLIANT" else ""}
  {"├─ 🟡 Zahlungsbedingung an der Grenze — Monitoring empfohlen." if result == "BORDERLINE" else ""}
  {"├─ ⛔ Zahlungsbedingung überschreitet die Risikopolitik. Anpassung oder Credit Manager-Genehmigung erforderlich." if result == "MISMATCH" else ""}
  └─ Ergebnis basiert auf S/4HANA: CreditRiskClass, CustomerPaymentTerms.
""")
    lines.append(_footer(
        "Tier 1 — Analyst" if result == "COMPLIANT" else "Tier 2 — Credit Manager",
        ["G1 Read-Only", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


def t4_payment_term_mismatch(customer: str = "CU10000001") -> str:
    """Sonderfall: Risikoklasse 04 + 60 Tage → MISMATCH."""
    risk_class    = "04"
    payment_days  = 60
    payment_term_code = "ZB60"

    validation   = validate_payment_terms(payment_days, risk_class)
    result       = validation["result"]
    reason       = validation["reason"]
    policy       = validation["policy"]
    policy_limit = RISK_CLASS_PAYMENT_TERM_LIMITS.get(risk_class, {})
    result_icon  = {"COMPLIANT": "✅", "BORDERLINE": "🟡", "MISMATCH": "⛔"}.get(result, "❓")

    lines = [_header(f"Zahlungsbedingungen-Validierung — Kunde {customer} [MISMATCH-SZENARIO]", "T4 PAYMENT TERM VALIDATION")]
    lines.append(f"""
  KUNDENPROFIL (simuliert: Risikoklasse 04)
  ├─ Kundennummer:         {customer}
  ├─ Risikoklasse:         {risk_class}  (KRITISCH)
  └─ Policy-Grenze:        {policy_limit.get("label", "Vorauszahlung")}

  BEANTRAGTE ZAHLUNGSBEDINGUNG
  ├─ Zahlungsbedingungscode:  {payment_term_code}
  └─ Zahlungsziel (Tage):     {payment_days} Tage

  VALIDIERUNGSERGEBNIS
  ├─ Status:               {result_icon}  {result}
  ├─ Begründung:           {reason}
  └─ Policy:               {policy}

  EMPFEHLUNG
  ├─ ⛔ Zahlungsziel von 60 Tagen ist für Risikoklasse 04 nicht zulässig.
  ├─ Policy verlangt ausschließlich Vorauszahlung für kritische Kunden.
  ├─ Eskalation zu Credit Manager (Tier 2) oder Ablehnung des Antrags.
  └─ Ergebnis basiert auf S/4HANA: CreditRiskClass, CustomerPaymentTerms.
""")
    lines.append(_footer(
        "Tier 2 — Credit Manager",
        ["G1 Read-Only", "G2 Limitcheck", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# T5 — Seasonal Financing Eligibility
# ─────────────────────────────────────────────────────────────────────────────

def t5_seasonal_financing(bp: str = "1000001") -> str:
    acct   = get_credit_account(bp)
    risk   = get_bp_risk_profile(bp)
    cw     = get_creditworthiness(bp)
    events = get_negative_events(bp)

    risk_class    = risk.get("CreditRiskClass", "N/A")
    dandb_rating  = cw.get("BPCreditStandingRating", None)
    dandb_date    = cw.get("BPCreditStandingDate", None)
    dandb_comment = cw.get("BPCreditStandingComment", "–")
    is_blocked    = acct.get("CreditAccountIsBlocked", False)
    neg_count     = len(events)

    age_check = check_dandb_data_age(dandb_date, max_age_days=90)
    is_stale  = age_check["is_stale"]
    age_days  = age_check.get("age_days", "N/A")

    score    = calculate_eligibility_score(risk_class, dandb_rating, is_blocked, neg_count)
    decision = get_eligibility_decision(score)

    decision_icon = {"ELIGIBLE": "✅", "CONDITIONAL": "🟡", "NOT ELIGIBLE": "⛔"}.get(decision, "❓")

    rc_pts = {"01": "40 Pkt (Exzellent)", "02": "25 Pkt (Gut)", "03": "10 Pkt (Mittel)", "04": "-20 Pkt (Kritisch)"}.get(risk_class, "0 Pkt")
    db_pts = "30 Pkt" if dandb_rating and dandb_rating.upper() in ("AAA","AA","A","BB+") else \
             "15 Pkt" if dandb_rating and dandb_rating.upper() in ("BBB","BB","B") else "-20 Pkt"

    lines = [_header(f"Saisonale Finanzierungs-Eignung — Business Partner {bp}", "T5 SEASONAL FINANCING ELIGIBILITY")]
    lines.append(f"""
  KUNDENPROFIL
  ├─ Business Partner:     {bp}
  ├─ Risikoklasse:         {risk_class}
  ├─ Kreditkonto gesperrt: {"Ja ⛔" if is_blocked else "Nein ✅"}
  └─ Negative Ereignisse:  {neg_count}

  D&B BONITÄTSDATEN (Guardrail G5)
  ├─ Rating:               {dandb_rating or "Nicht verfügbar"}
  ├─ Kommentar:            {dandb_comment}
  ├─ Datenalter:           {age_days} Tage
  └─ Datenstatus:          {"⛔ VERALTET (>90 Tage) — G5 ausgelöst" if is_stale else "✅ Aktuell (<90 Tage)"}

  SCORING
  ├─ Gesamtscore:          {score} / 100
  └─ Entscheidung:         {decision_icon}  {decision}

  SCOREBEITRÄGE
  ├─ Risikoklasse {risk_class}:   {rc_pts}
  ├─ D&B Rating {dandb_rating or "–"}:        {db_pts}
  ├─ Kreditblock:           {"−30 Pkt (gesperrt)" if is_blocked else "+20 Pkt (kein Block)"}
  └─ Negative Ereignisse:  {"+ 10 Pkt (keine)" if neg_count == 0 else f"−{20 * min(neg_count, 2)} Pkt ({neg_count} Ereignisse)"}

  EMPFEHLUNG
  {"├─ ✅ Eignung für saisonale Finanzierung bestätigt." if decision == "ELIGIBLE" else ""}
  {"├─ 🟡 Bedingt geeignet — individuelle Überprüfung durch Credit Manager (Tier 2) empfohlen." if decision == "CONDITIONAL" else ""}
  {"├─ ⛔ Nicht geeignet. Guardrail G4/G5 verhindert Freigabe." if decision == "NOT ELIGIBLE" else ""}
  └─ Entscheidungsgrundlage: CreditRiskClass, BPCreditStandingRating, CreditAccountIsBlocked.
""")
    lines.append(_footer(
        "Tier 1 — Analyst" if decision == "ELIGIBLE" else
        "Tier 2 — Credit Manager" if decision == "CONDITIONAL" else
        "Tier 3 — Credit Committee",
        ["G1 Read-Only", "G4 Überrückstand", "G5 D&B-Alter", "G8 Datenevidenz"]
    ))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Eskalationsmodell-Demo
# ─────────────────────────────────────────────────────────────────────────────

def demo_escalation_model() -> str:
    lines = [_header("Dreistufiges Eskalationsmodell & 8 Guardrails — Übersicht", "ESKALATIONSMODELL")]
    lines.append(f"""
  ┌──────────────────────────────────────────────────────────────────────┐
  │  TIER 1 — Credit Analyst (Standardfall)                             │
  │  Auslöser: Routineanalyse, Auslastung <70%, Konfidenz >70%          │
  │  Maßnahmen: Analyse, Empfehlung, Dokumentation                      │
  │  Beispiel: T4 COMPLIANT für Risikoklasse 02, T5 ELIGIBLE            │
  ├──────────────────────────────────────────────────────────────────────┤
  │  TIER 2 — Credit Manager (Mittleres Risiko)                         │
  │  Auslöser: Auslastung 70–90%, Konfidenz <70%, Kreditblock           │
  │  Maßnahmen: Genehmigung, Limitanpassung, Sicherheitenverhandlung    │
  │  Beispiel: T1 Kreditblock BP 2000002, T2 AMBER, T4 MISMATCH        │
  ├──────────────────────────────────────────────────────────────────────┤
  │  TIER 3 — Credit Committee (Hohes Risiko / Ausnahme)                │
  │  Auslöser: Exposition >Segmentlimit, Insolvenz, D&B-Alert           │
  │  Maßnahmen: Komitee-Entscheid, Policy-Ausnahme, Kontosperrung       │
  │  Beispiel: T5 NOT ELIGIBLE + D&B veraltet, T3 Insolvenzrisiko       │
  └──────────────────────────────────────────────────────────────────────┘

  8 AKTIVE GUARDRAILS
  ├─ G1 READ-ONLY:      Kein Write-Back in SAP-Systeme — nur Empfehlung
  ├─ G2 LIMITCHECK:     Kein Limit überschreiten ohne Eskalation
  ├─ G3 DCD-INSTRUMENT: Nur genehmigte Instrumente (LC, Bankgarantie ...)
  ├─ G4 ÜBERRÜCKSTAND:  Keine Saisonfinanzierung bei überfälligen Kunden
  ├─ G5 D&B-ALTER:      D&B-Daten müssen <90 Tage alt sein (T5)
  ├─ G6 KONFIDENZ:      Konfidenz <70% → automatisch Tier 2
  ├─ G7 DATENSCHUTZ:    Keine kundenseitige Datenweitergabe an Dritte
  └─ G8 EVIDENZ:        Jede Empfehlung braucht ≥1 S/4HANA-Datenfeld
""")
    lines.append(_footer("Tier 1–3 kontextabhängig", ["G1","G2","G3","G4","G5","G6","G7","G8"]))
    return "\n".join(lines)
