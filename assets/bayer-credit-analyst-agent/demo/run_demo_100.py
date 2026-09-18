"""
Bayer Credit Analyst Agent - 100 Demo-Fragen Runner
====================================================
python demo/run_demo_100.py --all
python demo/run_demo_100.py --question 42
python demo/run_demo_100.py --demo
python demo/run_demo_100.py --list
python demo/run_demo_100.py --export
"""
import argparse, os, sys, traceback, json

if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8","UTF8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

try:
    from simulation_engine import (
        t1_credit_block_explanation, t2_trm_utilization,
        t3_dcd_decision_support, t4_payment_term_validation,
        t4_payment_term_mismatch, t5_seasonal_financing,
        demo_escalation_model, SECTION
    )
    from questions_100 import RAW_QUESTIONS
except Exception as e:
    print(f"[FEHLER] Import: {e}"); traceback.print_exc(); sys.exit(1)

DIVIDER = "-" * 72

def _fn(q):
    t, kw, qtext = q["task"], q["kw"], q["q"].lower()
    # T1
    if t == "T1":
        return lambda: t1_credit_block_explanation(bp="2000002")
    # T2
    if t == "T2":
        if "2000002" in kw or "2000002" in qtext:
            return lambda: t2_trm_utilization(bp="2000002")
        return lambda: t2_trm_utilization(bp="1000001")
    # T3
    if t == "T3":
        bad = ["cheque","scheck","personal check","verboten","nicht zugelassen"]
        if any(b in qtext for b in bad) or any(b in kw for b in ["personal cheque","not approved"]):
            return lambda: t3_dcd_decision_support(bp="1000001", instrument="personal cheque")
        good_instruments = {
            "bankgarantie dcd": "bank guarantee",
            "bank guarantee dcd": "bank guarantee",
            "standby lc": "standby letter of credit",
            "standby letter": "standby letter of credit",
            "documentary collection": "documentary collection",
            "inkasso": "documentary collection",
            "vorauszahlung dcd": "advance payment",
            "advance payment dcd": "advance payment",
            "bestaetigt akkreditiv": "confirmed letter of credit",
            "confirmed lc": "confirmed letter of credit",
        }
        for key, instr in good_instruments.items():
            if key in qtext or key in " ".join(kw):
                return (lambda i=instr: lambda: t3_dcd_decision_support(bp="1000001", instrument=i))()
        return lambda: t3_dcd_decision_support(bp="1000001", instrument="irrevocable letter of credit")
    # T4
    if t == "T4":
        if any(x in qtext for x in ["60 tage","60 days","risikoklasse 04","mismatch"]) or "60 tage" in kw:
            return lambda: t4_payment_term_mismatch(customer="CU10000001")
        return lambda: t4_payment_term_validation(customer="CU10000001", bp="1000001")
    # T5
    if t == "T5":
        if "2000002" in qtext or "2000002" in kw or "not eligible 2000002" in kw:
            return lambda: t5_seasonal_financing(bp="2000002")
        return lambda: t5_seasonal_financing(bp="1000001")
    # ESK
    return lambda: demo_escalation_model()

QUESTIONS = [{**q, "fn": _fn(q)} for q in RAW_QUESTIONS]

def match(text):
    tl = text.lower()
    best, bscore = None, 0
    for q in QUESTIONS:
        score = sum(1 for kw in q["kw"] if kw in tl)
        if score > bscore:
            bscore, best = score, q
    return best if bscore > 0 else None

def sprint(txt):
    try: print(txt)
    except UnicodeEncodeError: print(txt.encode("ascii","replace").decode())

def run_q(q, pause=False):
    sprint(f"\n  FRAGE {q['id']:3d} [{q['task']}] {q['label']}")
    sprint(f"  >> {q['q']}\n")
    try:
        sprint(q["fn"]())
    except Exception as e:
        sprint(f"  [FEHLER]: {e}"); traceback.print_exc()
    if pause:
        try: input("\n  [Enter] ...")
        except: pass

def run_all(pause=False):
    for q in QUESTIONS:
        run_q(q, pause=pause)

def export_all():
    lines = ["BAYER CREDIT ANALYST AGENT - 100 Demo-Fragen\n", SECTION+"\n"]
    for q in QUESTIONS:
        lines.append(f"\n{DIVIDER}\nFRAGE {q['id']} | {q['task']} - {q['label']}\n{q['q']}\n\n")
        try: lines.append(q["fn"]())
        except Exception as e: lines.append(f"[FEHLER]: {e}")
        lines.append("\n")
    out = os.path.join(_DIR, "demo_output_100.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    sprint(f"\n  Gespeichert: {out}\n")

def list_questions():
    sprint(f"\n{SECTION}")
    sprint("  BAYER CREDIT ANALYST AGENT - 100 Demo-Fragen")
    sprint(SECTION)
    cur_task = None
    for q in QUESTIONS:
        if q["task"] != cur_task:
            cur_task = q["task"]
            sprint(f"\n  [{cur_task}]")
        sprint(f"  {q['id']:3d}. {q['q'][:75]}{'...' if len(q['q'])>75 else ''}")
    sprint(f"\n{SECTION}\n")

def demo_mode():
    sprint(f"\n{SECTION}")
    sprint("  BAYER CREDIT ANALYST AGENT - Demo-Modus (100 Fragen)")
    sprint("  Frage eingeben, Nummer (1-100), 'alle', oder 'exit'\n")
    sprint("  Beispiele:")
    for q in QUESTIONS[:5]:
        sprint(f"    [{q['id']}] {q['q']}")
    sprint(f"{SECTION}\n")
    while True:
        try: user = input("  Frage: ").strip()
        except: break
        if not user: continue
        if user.lower() in ("exit","quit","99"): break
        if user.lower() in ("alle","all","0"):
            run_all(pause=False); continue
        if user.lower() == "list":
            list_questions(); continue
        try:
            num = int(user)
            qs = [q for q in QUESTIONS if q["id"]==num]
            if qs: run_q(qs[0], pause=False); continue
            else: sprint(f"  Nummer {num} nicht gefunden (1-100)")
        except ValueError:
            pass
        m = match(user)
        if m:
            sprint(f"\n  Erkannte Frage [{m['id']}]: {m['label']}\n")
            run_q(m, pause=False)
        else:
            sprint("  Nicht erkannt. Probieren Sie: kreditblock | auslastung | akkreditiv | zahlungsbedingungen | saisonale | eskalation")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--all",      action="store_true")
    p.add_argument("--question", type=int)
    p.add_argument("--export",   action="store_true")
    p.add_argument("--demo",     action="store_true")
    p.add_argument("--list",     action="store_true")
    args = p.parse_args()
    if args.list:     list_questions()
    elif args.export: export_all()
    elif args.all:    run_all(pause=False)
    elif args.question:
        qs = [q for q in QUESTIONS if q["id"]==args.question]
        if qs: run_q(qs[0])
        else: sprint(f"Frage {args.question} nicht gefunden.")
    elif args.demo:   demo_mode()
    else:             demo_mode()

if __name__=="__main__":
    main()
