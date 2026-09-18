"""
Bayer Credit Analyst Agent — Interaktive Testumgebung
======================================================
Simuliert realistische Agentenantworten ohne LLM-Aufruf auf Basis von mcp-mock.json.

Aufruf:
    python demo/run_demo.py                 # Interaktiver Modus (Menü)
    python demo/run_demo.py --all           # Alle 10 Demo-Fragen automatisch
    python demo/run_demo.py --question 3    # Einzelne Frage (1–10)
    python demo/run_demo.py --export        # Alle Antworten → demo/demo_output.txt
    python demo/run_demo.py --demo          # Demo-Modus: freie Texteingabe
"""
import argparse
import os
import sys
import traceback

# ── Encoding fix: UTF-8 erzwingen ─────────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── robuster Import ────────────────────────────────────────────────────────────
try:
    from simulation_engine import (
        t1_credit_block_explanation,
        t2_trm_utilization,
        t3_dcd_decision_support,
        t4_payment_term_validation,
        t4_payment_term_mismatch,
        t5_seasonal_financing,
        demo_escalation_model,
        SECTION,
    )
except Exception as e:
    print(f"[FEHLER] Simulation Engine konnte nicht geladen werden: {e}")
    traceback.print_exc()
    sys.exit(1)

DIVIDER = "─" * 72

# ─────────────────────────────────────────────────────────────────────────────
# FRAGENKATALOG — 10 sinnvolle Demo-Fragen
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    {
        "id": 1, "task": "T1", "label": "Kreditblock-Erklärung",
        "question": "Warum ist Business Partner 2000002 (Agro Solutions) gesperrt und welche Aufträge sind betroffen?",
        "keywords": ["gesperrt", "kreditblock", "block", "2000002", "agro", "aufträge", "sperr"],
        "fn": lambda: t1_credit_block_explanation(bp="2000002"),
    },
    {
        "id": 2, "task": "T2", "label": "TRM Utilization — Grüner Bereich",
        "question": "Wie hoch ist die Kreditlimit-Auslastung von BP 1000001 und welche Treasury-Sicherheiten sind hinterlegt?",
        "keywords": ["auslastung", "1000001", "sicherheiten", "treasury", "trm", "limit"],
        "fn": lambda: t2_trm_utilization(bp="1000001"),
    },
    {
        "id": 3, "task": "T2", "label": "TRM Utilization — Amber-Bereich",
        "question": "BP 2000002 hat eine hohe Auslastung — bitte TRM-Bewertung mit Risikoampel erstellen.",
        "keywords": ["2000002", "auslastung", "ampel", "trm bewertung", "risikoampel"],
        "fn": lambda: t2_trm_utilization(bp="2000002"),
    },
    {
        "id": 4, "task": "T3", "label": "DCD — Akkreditiv genehmigt",
        "question": "Kunde 1000001 möchte ein Akkreditiv (Letter of Credit) hinterlegen — ist das zulässig?",
        "keywords": ["akkreditiv", "letter of credit", "lc", "zulässig", "hinterlegen", "dcd", "1000001"],
        "fn": lambda: t3_dcd_decision_support(bp="1000001", instrument="irrevocable letter of credit"),
    },
    {
        "id": 5, "task": "T3", "label": "DCD — Personal Cheque abgelehnt",
        "question": "Ein Kunde schlägt einen 'Personal Cheque' als DCD-Instrument vor — ist das gemäß Bayer-Richtlinie zulässig?",
        "keywords": ["cheque", "check", "scheck", "personal", "dcd instrument", "richtlinie"],
        "fn": lambda: t3_dcd_decision_support(bp="1000001", instrument="personal cheque"),
    },
    {
        "id": 6, "task": "T4", "label": "Payment Terms — Compliant",
        "question": "Welche Zahlungsbedingungen hat Kunde CU10000001 vereinbart und sind diese konform mit seiner Risikoklasse?",
        "keywords": ["zahlungsbedingungen", "cu10000001", "konform", "zahlungsziel", "payment", "vereinbart"],
        "fn": lambda: t4_payment_term_validation(customer="CU10000001", bp="1000001"),
    },
    {
        "id": 7, "task": "T4", "label": "Payment Terms — Mismatch",
        "question": "Kunde CU10000001 (Risikoklasse 04 — kritisch) möchte 60 Tage Zahlungsziel — ist das policy-konform?",
        "keywords": ["60 tage", "risikoklasse 04", "kritisch", "policy", "mismatch", "60"],
        "fn": lambda: t4_payment_term_mismatch(customer="CU10000001"),
    },
    {
        "id": 8, "task": "T5", "label": "Seasonal Financing — Eligible",
        "question": "Ist Business Partner 1000001 für das saisonale Frühjahrs-Finanzierungsprogramm 2025 geeignet?",
        "keywords": ["saisonale", "frühjahr", "finanzierung", "1000001", "geeignet", "eligible", "2025"],
        "fn": lambda: t5_seasonal_financing(bp="1000001"),
    },
    {
        "id": 9, "task": "T5", "label": "Seasonal Financing — Not Eligible",
        "question": "Business Partner 2000002 (gesperrt, Risikoklasse 04) beantragt saisonale Finanzierung — was empfiehlt der Agent?",
        "keywords": ["2000002", "saisonal", "finanzierung", "not eligible", "empfiehlt"],
        "fn": lambda: t5_seasonal_financing(bp="2000002"),
    },
    {
        "id": 10, "task": "ESK", "label": "Eskalationsmodell & 8 Guardrails",
        "question": "Erkläre das dreistufige Eskalationsmodell und die acht Guardrails des Bayer Credit Analyst Agenten.",
        "keywords": ["eskalation", "guardrail", "tier", "dreistufig", "acht", "modell"],
        "fn": lambda: demo_escalation_model(),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Keyword-Matching für freie Texteingabe
# ─────────────────────────────────────────────────────────────────────────────

def match_question(text: str):
    """Gibt die beste passende Frage zurück oder None."""
    text_lower = text.lower()
    best_match = None
    best_score = 0
    for q in QUESTIONS:
        score = sum(1 for kw in q["keywords"] if kw in text_lower)
        if score > best_score:
            best_score = score
            best_match = q
    return best_match if best_score > 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# Ausgabe-Helfer
# ─────────────────────────────────────────────────────────────────────────────

def safe_print(text: str):
    """Gibt Text aus, ersetzt nicht-darstellbare Zeichen statt abzubrechen."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def print_menu():
    safe_print(f"\n{SECTION}")
    safe_print("  🏦  BAYER CREDIT ANALYST AGENT — Testumgebung  (Simuliert / Read-Only)")
    safe_print(SECTION)
    safe_print("  Wählen Sie eine Demo-Frage oder tippen Sie Ihre Frage frei ein:\n")
    for q in QUESTIONS:
        short = q["question"][:72] + ("…" if len(q["question"]) > 72 else "")
        safe_print(f"  [{q['id']:>2}]  {q['task']:4}  {q['label']}")
        safe_print(f"        \"{short}\"")
        safe_print("")
    safe_print("  [ 0]  Alle Fragen automatisch durchlaufen")
    safe_print("  [99]  Beenden")
    safe_print(SECTION)


def run_question(q: dict, pause: bool = True):
    safe_print(f"\n  ➤  FRAGE {q['id']}: {q['question']}\n")
    try:
        result = q["fn"]()
        safe_print(result)
    except Exception as e:
        safe_print(f"\n  [FEHLER bei Frage {q['id']}]: {e}")
        traceback.print_exc()
    if pause:
        try:
            input("\n  [Enter] für nächste Frage ...")
        except (KeyboardInterrupt, EOFError):
            pass


def run_all(pause: bool = True):
    for q in QUESTIONS:
        run_question(q, pause=pause)


def export_all():
    lines = [
        "BAYER CREDIT ANALYST AGENT — Demo-Ausgabe (alle 10 Fragen)\n",
        SECTION + "\n"
    ]
    for q in QUESTIONS:
        lines.append(f"\n{'─'*72}\nFRAGE {q['id']} | {q['task']} — {q['label']}\n")
        lines.append(f"Frage: {q['question']}\n\n")
        try:
            lines.append(q["fn"]())
        except Exception as e:
            lines.append(f"[FEHLER]: {e}")
        lines.append("\n")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    safe_print(f"\n  ✅ Demo-Ausgabe gespeichert: {out}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Demo-Modus: freie Texteingabe
# ─────────────────────────────────────────────────────────────────────────────

def run_demo_mode():
    safe_print(f"\n{SECTION}")
    safe_print("  🏦  BAYER CREDIT ANALYST AGENT — Demo-Modus")
    safe_print("  Tippen Sie Ihre Frage frei ein. 'exit' zum Beenden.")
    safe_print(SECTION + "\n")
    safe_print("  Beispiel-Fragen:")
    for q in QUESTIONS:
        safe_print(f"    • {q['question']}")
    safe_print("")

    while True:
        try:
            user_input = input("\n  🔎 Ihre Frage: ").strip()
        except (KeyboardInterrupt, EOFError):
            safe_print("\n  Auf Wiedersehen.\n")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "beenden", "99"):
            safe_print("\n  Auf Wiedersehen.\n")
            break
        if user_input in ("0", "alle", "all"):
            run_all(pause=False)
            continue

        # Zuerst: Zahl eingegeben?
        try:
            num = int(user_input)
            matches = [q for q in QUESTIONS if q["id"] == num]
            if matches:
                run_question(matches[0], pause=False)
                continue
        except ValueError:
            pass

        # Keyword-Matching auf freien Text
        matched = match_question(user_input)
        if matched:
            safe_print(f"\n  ✅ Erkannte Frage: [{matched['id']}] {matched['label']}\n")
            run_question(matched, pause=False)
        else:
            safe_print("\n  ❓ Frage nicht erkannt. Versuchen Sie eine der folgenden Schlüsselwörter:")
            safe_print("     kreditblock | auslastung | akkreditiv | zahlungsbedingungen | saisonale | eskalation")
            safe_print("  Oder geben Sie eine Zahl (1–10) ein.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bayer Credit Analyst Agent — Testumgebung")
    parser.add_argument("--all",      action="store_true", help="Alle Fragen automatisch")
    parser.add_argument("--question", type=int,            help="Einzelne Frage (1–10)")
    parser.add_argument("--export",   action="store_true", help="Ausgabe in demo_output.txt")
    parser.add_argument("--demo",     action="store_true", help="Demo-Modus: freie Texteingabe")
    args = parser.parse_args()

    if args.export:
        export_all()
        return

    if args.all:
        run_all(pause=False)
        return

    if args.question:
        matches = [q for q in QUESTIONS if q["id"] == args.question]
        if not matches:
            safe_print(f"  ⛔ Frage {args.question} nicht gefunden (gültig: 1–10).")
            sys.exit(1)
        run_question(matches[0], pause=False)
        return

    if args.demo:
        run_demo_mode()
        return

    # Standard: interaktives Menü
    while True:
        print_menu()
        try:
            choice = input("  Ihre Wahl (Zahl oder Frage): ").strip()
        except (KeyboardInterrupt, EOFError):
            safe_print("\n  Auf Wiedersehen.\n")
            break

        if choice == "99" or choice.lower() in ("exit", "beenden"):
            safe_print("\n  Auf Wiedersehen.\n")
            break
        elif choice == "0":
            run_all(pause=True)
        else:
            # Zahl?
            try:
                num = int(choice)
                matches = [q for q in QUESTIONS if q["id"] == num]
                if matches:
                    run_question(matches[0], pause=True)
                else:
                    safe_print(f"\n  ⛔ Ungültige Nummer: {choice}")
            except ValueError:
                # Freie Texteingabe im Menü
                matched = match_question(choice)
                if matched:
                    safe_print(f"\n  ✅ Erkannte Frage: [{matched['id']}] {matched['label']}\n")
                    run_question(matched, pause=True)
                else:
                    safe_print(f"\n  ❓ Nicht erkannt. Bitte Zahl (1–10) oder Schlüsselwort eingeben.")


if __name__ == "__main__":
    main()
