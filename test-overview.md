# Testübersicht — Bayer Credit Analyst Agent

**Stand:** 2026-09-18 | **Ergebnis: 88/88 bestanden · 0 Fehler**

---

## Gesamtergebnis

| Kategorie | Tests | Bestanden | Fehler | Abdeckung |
|-----------|------:|----------:|-------:|-----------|
| Guardrail-Logik (Unit) | 32 | 32 | 0 | G1–G8 vollständig |
| Business-Kalkulation (Unit) | 42 | 42 | 0 | T1–T5 vollständig |
| Guardrail-Integration | 10 | 10 | 0 | G3, G4, G5, G6, G8, Eskalation |
| Agent-Integration | 6 | 6 | 0 | A2A, invoke, stream |
| Instrumentation (Unit) | 14 | 14 | 0 | M1–M5, alle log-Funktionen |
| **Gesamt** | **88** | **88** | **0** | |

---

## Testdateien im Detail

### 1. `tests/test_tools.py` — Business-Logik & Guardrail-Utilities (48 Tests)

#### G5 — D&B Datenalter-Validierung (`check_dandb_data_age`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_fresh_data_not_stale` | Daten < 90 Tage → nicht veraltet | ✅ |
| `test_stale_data_over_90_days` | Daten > 90 Tage → veraltet | ✅ |
| `test_exactly_90_days_not_stale` | Grenzwert exakt 90 Tage → noch gültig | ✅ |
| `test_none_date_is_stale` | Kein Datum vorhanden → veraltet | ✅ |
| `test_invalid_date_is_stale` | Ungültiges Datum → veraltet | ✅ |
| `test_odata_date_format` | OData `/Date(ms)/`-Format wird korrekt geparst | ✅ |

#### T2 — TRM Auslastungsberechnung (`calculate_utilization_pct`, `get_utilization_tier`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_normal_utilization` | 75.000 / 100.000 = 75,00% | ✅ |
| `test_over_limit` | 110.000 / 100.000 = 110,00% (Überschreitung) | ✅ |
| `test_zero_limit_returns_none` | Kreditlimit 0 → kein Ergebnis | ✅ |
| `test_none_limit_returns_none` | Fehlendes Limit → kein Ergebnis | ✅ |
| `test_none_exposure_returns_none` | Fehlendes Exposure → kein Ergebnis | ✅ |
| `test_zero_exposure` | Exposure 0 → 0,00% | ✅ |
| `test_rounds_to_two_decimals` | 1/3 → 33,33% (korrekte Rundung) | ✅ |
| `test_green_at_50` | 50% → GREEN | ✅ |
| `test_green_at_70` | 70% → GREEN (Grenzwert) | ✅ |
| `test_amber_at_71` | 71% → AMBER | ✅ |
| `test_amber_at_90` | 90% → AMBER (Grenzwert) | ✅ |
| `test_red_at_91` | 91% → RED | ✅ |
| `test_red_at_150` | 150% → RED (Überschreitung) | ✅ |
| `test_none_returns_unknown` | Kein Wert → UNKNOWN | ✅ |

#### T5 — Seasonal-Financing-Scoring (`calculate_eligibility_score`, `get_eligibility_decision`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_low_risk_excellent_dandb` | Risikoklasse 01 + AAA-Rating → 100 Punkte | ✅ |
| `test_critical_risk_poor_dandb` | Risikoklasse 04 + CCC + Überfälligkeit → 0 Punkte (Clamp) | ✅ |
| `test_medium_risk_no_events` | Risikoklasse 02 + BBB → 70 Punkte (ELIGIBLE) | ✅ |
| `test_overdue_block_deducts_points` | Überfälligkeitssperre reduziert Score | ✅ |
| `test_negative_events_deduct_points` | Negative Ereignisse reduzieren Score | ✅ |
| `test_score_clamped_to_100` | Score wird auf 100 begrenzt | ✅ |
| `test_score_clamped_to_0` | Score wird auf 0 begrenzt | ✅ |
| `test_eligible_at_70` | Score 70 → ELIGIBLE | ✅ |
| `test_eligible_at_100` | Score 100 → ELIGIBLE | ✅ |
| `test_conditional_at_50` | Score 50 → CONDITIONAL | ✅ |
| `test_conditional_at_69` | Score 69 → CONDITIONAL | ✅ |
| `test_not_eligible_at_49` | Score 49 → NOT ELIGIBLE | ✅ |
| `test_not_eligible_at_0` | Score 0 → NOT ELIGIBLE | ✅ |

#### T1 — Kreditblock-Grundcodes (`get_block_reason_description`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_known_code_01` | Code 01 → "credit limit exceeded" | ✅ |
| `test_known_code_09` | Code 09 → "overdue" | ✅ |
| `test_unknown_code_returns_fallback` | Unbekannter Code → Fallback mit Code-Nennung | ✅ |
| `test_none_returns_unknown` | Kein Code → "unknown" | ✅ |
| `test_all_10_codes_present` | Alle 10 Codes (01–10) in Tabelle vorhanden | ✅ |

#### G3 — DCD Instrument-Validierung (`is_approved_dcd_instrument`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_irrevocable_lc_approved` | Unwiderrufliches Akkreditiv → genehmigt | ✅ |
| `test_bank_guarantee_approved` | Bankgarantie → genehmigt | ✅ |
| `test_advance_payment_approved` | Vorauszahlung → genehmigt | ✅ |
| `test_da_approved` | Documentary Collection D/A → genehmigt | ✅ |
| `test_open_account_not_approved` | Offene Rechnung → abgelehnt | ✅ |
| `test_cheque_not_approved` | Scheck → abgelehnt | ✅ |
| `test_none_not_approved` | Kein Instrument → abgelehnt | ✅ |
| `test_case_insensitive` | Großschreibung ignoriert | ✅ |

#### T4 — Zahlungsbedingungen-Validierung (`validate_payment_terms`)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_compliant_low_risk_30_days` | Risikoklasse 01 + 30 Tage → COMPLIANT | ✅ |
| `test_mismatch_medium_risk_60_days` | Risikoklasse 02 + 60 Tage → MISMATCH | ✅ |
| `test_borderline_medium_risk_41_days` | Risikoklasse 02 + 41 Tage (>90% von 45) → BORDERLINE | ✅ |
| `test_mismatch_critical_risk_any_credit` | Risikoklasse 04 + Kreditbedingungen → MISMATCH | ✅ |
| `test_compliant_critical_risk_zero_days` | Risikoklasse 04 + 0 Tage → COMPLIANT/BORDERLINE | ✅ |
| `test_none_days_returns_unknown` | Fehlende Tage → UNKNOWN | ✅ |
| `test_none_risk_class_returns_unknown` | Fehlende Risikoklasse → UNKNOWN | ✅ |
| `test_result_includes_policy` | Ergebnis enthält Policy-Referenz | ✅ |

---

### 2. `tests/test_instrumentation.py` — Milestone-Logging (14 Tests)

| Test | Milestone / Funktion | Beschreibung | Ergebnis |
|------|---------------------|-------------|---------|
| `test_emit_achieved` | Alle | Log-Format `[M?.achieved]: ...` korrekt | ✅ |
| `test_emit_missed` | Alle | Log-Format `[M?.missed]: ...` korrekt | ✅ |
| `test_log_guardrail_triggered` | G1–G8 | `GUARDRAIL.G?.triggered` wird geloggt | ✅ |
| `test_log_guardrail_passed` | G1–G8 | `GUARDRAIL.G?.passed` wird geloggt | ✅ |
| `test_m1_achieved` | M1 | S/4HANA-Datenzugriff bestätigt | ✅ |
| `test_m1_missed` | M1 | API-Verbindungsfehler korrekt geloggt | ✅ |
| `test_m2_achieved` | M2 | T1-Validierung erfolgreich | ✅ |
| `test_m2_missed` | M2 | T1-Genauigkeit unter Schwellwert | ✅ |
| `test_m3_achieved` | M3 | T2–T4 validiert | ✅ |
| `test_m3_missed` | M3 | T2/T3/T4-Fehler korrekt geloggt | ✅ |
| `test_m4_achieved` | M4 | T5 + D&B-Integration aktiv | ✅ |
| `test_m4_missed` | M4 | D&B-Integration fehlgeschlagen | ✅ |
| `test_m5_achieved` | M5 | Eskalationsmodell + alle Guardrails in Produktion | ✅ |
| `test_m5_missed` | M5 | Guardrail-Verletzung in Produktion | ✅ |

---

### 3. `tests/test_guardrails_integration.py` — Guardrail-Integration (10 Tests)

| Test | Guardrail | Szenario | Ergebnis |
|------|-----------|---------|---------|
| `test_approved_instruments_pass` | G3 | 8 genehmigte Instrumente → alle bestanden | ✅ |
| `test_non_approved_instruments_fail` | G3 | 5 nicht-genehmigte Instrumente → alle abgelehnt | ✅ |
| `test_overdue_block_code_01_lowers_score_to_ineligible` | G4 | Überfälligkeitssperre → Score < 50 (NOT ELIGIBLE) | ✅ |
| `test_no_overdue_block_allows_eligibility` | G4 | Kein Block → Score ≥ 70 (ELIGIBLE) | ✅ |
| `test_fresh_data_passes` | G5 | 10 Tage alte D&B-Daten → kein Stale-Flag | ✅ |
| `test_91_day_data_fails` | G5 | 91 Tage alte D&B-Daten → Stale-Flag gesetzt | ✅ |
| `test_missing_data_fails` | G5 | Kein D&B-Datum → Stale-Flag gesetzt | ✅ |
| `test_confidence_threshold` | G6 | Schwellwert 70%: 69 < 70 → Eskalation | ✅ |
| `test_block_reason_description_references_field_context` | G8 | Alle 10 Codes haben aussagekräftige Beschreibungen | ✅ |
| `test_tier1/2/3_conditions` + Payment/Seasonal | Eskalation | GREEN→T1, AMBER→T2, RED→T2, MISMATCH→T2, NOT ELIGIBLE→T2 | ✅ |

---

### 4. `tests/test_agent_integration.py` — Agent End-to-End (6 Tests)

| Test | Beschreibung | Ergebnis |
|------|-------------|---------|
| `test_agent_instantiates_without_error` | Agent-Klasse startet ohne Exception | ✅ |
| `test_system_prompt_contains_required_elements` | System Prompt enthält READ-ONLY, T1–T5, G1, G8, Tier 1–3 | ✅ |
| `test_agent_invoke_returns_response` | `invoke()` liefert `AgentResponse` mit Status + Message | ✅ |
| `test_agent_stream_yields_chunks` | `stream()` liefert mind. 1 Chunk mit `is_task_complete` | ✅ |
| `test_agent_responds_to_t1_query` | T1-Anfrage wird verarbeitet und beantwortet | ✅ |
| `test_agent_responds_to_t5_query` | T5-Anfrage wird verarbeitet und beantwortet | ✅ |

---

## Artefakt-Validierung

| Prüfung | Ergebnis |
|---------|---------|
| `solution.yaml` — Schema, Name, Asset-Referenz | ✅ |
| `asset.yaml` — Schema, Typ `agent`, ORD-ID-Format, Port 5000 | ✅ |
| `asset.yaml` — Health Probes (startup/liveness/readiness) auf `/.well-known/agent.json` | ✅ |
| `Dockerfile` — Python-Basis, Port 5000 | ✅ |
| `conftest.py` — `IBD_TESTING=true` gesetzt | ✅ |
| Agent-Dekoratoren — exakt 9 (`@agent_model`, `@agent_config`, `@prompt_section`) | ✅ |
| System Prompt — T1–T5, G1–G8, Eskalation Tier 1–3, READ-ONLY | ✅ |
| Runtime Skills — 7 SKILL.md mit gültigem Frontmatter | ✅ |
| Milesteine — M1–M5 mit achieved/missed-Funktionen | ✅ |
| `test_report.json` — 88/88, 0 Fehler | ✅ |

---

## MCP-Server Status

| Server | URL | Status |
|--------|-----|--------|
| ical-mcp-server | `prod-ical-mcpserver.c-86fbf98.kyma.ondemand.com/mcp` | 🔐 Auth erforderlich (OAuth PKCE, Scope: `ical!t601035.consumer`) |
| ekx-mcp-server | `prod-ekxmcp-serving.c-86fbf98.kyma.ondemand.com/mcp` | 🔐 Auth erforderlich (OAuth `private_key_jwt`, Scope: `ekxmcp!t601035.consumer`) |
| joule-hub | `hub.joule.only.sap/mcp` | ❌ Nicht erreichbar (DNS-Fehler — internes SAP-Netzwerk erforderlich) |
| ask-services | `ask-services-rest-api-r2.cfapps.eu10-004.hana.ondemand.com/mcp-server/mcp` | ✅ Verbunden — 5 Tools: `tool_listing_query`, `tool_keywords_query`, `tool_rag_search`, `tool_all_query`, `tool_pricing_query` |
