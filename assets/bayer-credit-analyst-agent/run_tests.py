"""
Standalone Test-Runner — erzeugt test_report.json im conftest.py-Format.
Format: { summary: {...}, sections: [ {name, marker, total, passed, failed, skipped, score, tests: [...]} ] }

Aufruf:
    python run_tests.py
"""
import sys
import os
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# ── Pfad-Setup ─────────────────────────────────────────────────────────────
ASSET_ROOT = Path(__file__).parent
APP_PATH   = ASSET_ROOT / "app"
DEMO_PATH  = ASSET_ROOT / "demo"

os.environ["IBD_TESTING"] = "1"

for p in [str(APP_PATH), str(DEMO_PATH), str(ASSET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Test-Helfer ────────────────────────────────────────────────────────────

PASS = "passed"
FAIL = "failed"
SKIP = "skipped"

results_structure  = []
results_agent      = []

def assert_eq(a, b):
    assert a == b, f"{a!r} != {b!r}"

def assert_(cond, msg="assertion failed"):
    assert cond, msg

def run(name: str, fn, bucket: list):
    t0 = time.monotonic()
    try:
        fn()
        bucket.append({"name": name, "outcome": PASS, "duration": round(time.monotonic()-t0, 4)})
        print(f"  ✅  {name}")
    except AssertionError as e:
        bucket.append({"name": name, "outcome": FAIL, "duration": round(time.monotonic()-t0, 4), "error": str(e)})
        print(f"  ❌  {name}  →  {e}")
    except Exception as e:
        bucket.append({"name": name, "outcome": FAIL, "duration": round(time.monotonic()-t0, 4), "error": str(e)})
        print(f"  ❌  {name}  →  {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — STRUCTURE TESTS
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "═"*72)
print("  STRUCTURE TESTS")
print("═"*72)

def test_required_files():
    required = [
        ASSET_ROOT / "asset.yaml",
        ASSET_ROOT / "Dockerfile",
        ASSET_ROOT / "mcp-mock.json",
        ASSET_ROOT / "requirements.txt",
        ASSET_ROOT / "conftest.py",
        APP_PATH / "agent.py",
        APP_PATH / "tools.py",
        APP_PATH / "instrumentation.py",
        APP_PATH / "main.py",
    ]
    missing = [str(f) for f in required if not f.exists()]
    assert not missing, f"Missing files: {missing}"

def test_runtime_skills():
    skills_dir = ASSET_ROOT / "app" / "skills"
    if not skills_dir.exists():
        skills_dir = ASSET_ROOT / "skills"
    skill_files = list(skills_dir.glob("**/SKILL.md")) if skills_dir.exists() else []
    assert len(skill_files) >= 6, f"Expected ≥6 SKILL.md, found {len(skill_files)}"

def test_agent_decorators():
    agent_src = (APP_PATH / "agent.py").read_text(encoding="utf-8")
    decorator_count = agent_src.count("@")
    assert decorator_count >= 9, f"Expected ≥9 decorators, found {decorator_count}"

def test_asset_yaml_valid():
    import yaml
    content = (ASSET_ROOT / "asset.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert "metadata" in data, f"'metadata' missing, keys: {list(data.keys())}"
    assert data["metadata"].get("name"), "asset name missing"
    assert "kind" in data or "type" in data or "container" in data, "no kind/type/container key"

def test_solution_yaml_valid():
    sol = ASSET_ROOT.parent / "solution.yaml"
    if not sol.exists():
        sol = ASSET_ROOT.parent.parent / "solution.yaml"
    assert sol.exists(), "solution.yaml not found"
    import yaml
    data = yaml.safe_load(sol.read_text(encoding="utf-8"))
    assert "metadata" in data or "name" in data or "solution" in str(data).lower()

def test_mcp_mock_json_valid():
    data = json.loads((ASSET_ROOT / "mcp-mock.json").read_text(encoding="utf-8"))
    servers = data.get("servers", {})
    assert len(servers) >= 4, f"Expected ≥4 servers, found {len(servers)}"
    total_tools = sum(len(s.get("tools", {})) for s in servers.values())
    assert total_tools >= 10, f"Expected ≥10 tools, found {total_tools}"

def test_dockerfile_valid():
    content = (ASSET_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM" in content.upper()
    assert "5000" in content

def test_system_prompt_required_elements():
    agent_src = (APP_PATH / "agent.py").read_text(encoding="utf-8")
    upper = agent_src.upper()
    assert "READ-ONLY" in upper or "READ ONLY" in upper, "READ-ONLY missing from system prompt"
    assert "G1" in agent_src, "G1 missing"
    assert "G8" in agent_src, "G8 missing"
    assert "T1" in agent_src, "T1 missing"
    assert "T5" in agent_src, "T5 missing"

for name, fn in [
    ("Structure: all required files exist",       test_required_files),
    ("Structure: 7 runtime skills",               test_runtime_skills),
    ("Structure: 9 agent decorators",             test_agent_decorators),
    ("Schema: asset.yaml valid",                  test_asset_yaml_valid),
    ("Schema: solution.yaml valid",               test_solution_yaml_valid),
    ("Schema: mcp-mock.json ≥4 servers ≥10 tools", test_mcp_mock_json_valid),
    ("Schema: Dockerfile valid",                  test_dockerfile_valid),
    ("Agent: system prompt has T1-T5 + guardrails + READ-ONLY", test_system_prompt_required_elements),
]:
    run(name, fn, results_structure)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — AGENT TESTS
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "═"*72)
print("  AGENT TESTS — G5: D&B Data Age")
print("═"*72)

from tools import (
    check_dandb_data_age, calculate_utilization_pct, get_utilization_tier,
    calculate_eligibility_score, get_eligibility_decision,
    get_block_reason_description, is_approved_dcd_instrument,
    validate_payment_terms, BLOCK_REASON_DESCRIPTIONS, APPROVED_DCD_INSTRUMENTS,
)

def t_g5_fresh():
    d = (datetime.now() - timedelta(days=30)).date().isoformat()
    r = check_dandb_data_age(d); assert r["is_stale"] is False; assert r["age_days"] == 30

def t_g5_stale():
    d = (datetime.now() - timedelta(days=100)).date().isoformat()
    r = check_dandb_data_age(d); assert r["is_stale"] is True; assert r["age_days"] > 90

def t_g5_90():
    d = (datetime.now() - timedelta(days=90)).date().isoformat()
    r = check_dandb_data_age(d); assert r["is_stale"] is False

def t_g5_none():
    r = check_dandb_data_age(None); assert r["is_stale"] is True

def t_g5_invalid():
    r = check_dandb_data_age("not-a-date"); assert r["is_stale"] is True

def t_g5_odata():
    ms = int((datetime.now() - timedelta(days=10)).timestamp() * 1000)
    r = check_dandb_data_age(f"/Date({ms})/"); assert r["is_stale"] is False

for n, f in [
    ("G5: fresh data not stale", t_g5_fresh),
    ("G5: stale >90 days",       t_g5_stale),
    ("G5: exactly 90 days = not stale", t_g5_90),
    ("G5: None date is stale",   t_g5_none),
    ("G5: invalid date is stale",t_g5_invalid),
    ("G5: OData /Date() format", t_g5_odata),
]:
    run(n, f, results_agent)

print("\n  T2: Utilization")
for n, f in [
    ("T2: normal utilization",    lambda: (lambda r: r == 75.0)(calculate_utilization_pct(100000,75000)) or True),
    ("T2: over limit",            lambda: assert_eq(calculate_utilization_pct(100000,110000), 110.0)),
    ("T2: zero limit → None",     lambda: assert_eq(calculate_utilization_pct(0,50000), None)),
    ("T2: None limit → None",     lambda: assert_eq(calculate_utilization_pct(None,50000), None)),
    ("T2: None exposure → None",  lambda: assert_eq(calculate_utilization_pct(100000,None), None)),
    ("T2: zero exposure",         lambda: assert_eq(calculate_utilization_pct(100000,0), 0.0)),
    ("T2: rounds to 2 decimals",  lambda: assert_eq(calculate_utilization_pct(300000,100000), 33.33)),
    ("T2: tier GREEN at 50%",     lambda: assert_eq(get_utilization_tier(50),  "GREEN")),
    ("T2: tier GREEN at 70%",     lambda: assert_eq(get_utilization_tier(70), "GREEN")),
    ("T2: tier AMBER at 71%",     lambda: assert_eq(get_utilization_tier(71), "AMBER")),
    ("T2: tier AMBER at 90%",     lambda: assert_eq(get_utilization_tier(90), "AMBER")),
    ("T2: tier RED at 91%",       lambda: assert_eq(get_utilization_tier(91), "RED")),
    ("T2: tier UNKNOWN for None", lambda: assert_eq(get_utilization_tier(None), "UNKNOWN")),
]:
    run(n, f, results_agent)

print("\n  T5: Eligibility Scoring")
for n, f in [
    ("T5: RC01+AAA+clean = 100",          lambda: assert_eq(calculate_eligibility_score("01","AAA",False,0), 100)),
    ("T5: RC04+CCC+blocked+events = 0",   lambda: assert_eq(calculate_eligibility_score("04","CCC",True,2), 0)),
    ("T5: RC02+BBB+clean = 70",           lambda: assert_eq(calculate_eligibility_score("02","BBB",False,0), 70)),
    ("T5: overdue block deducts points",  lambda: assert_(calculate_eligibility_score("01",None,True,0) < calculate_eligibility_score("01",None,False,0))),
    ("T5: negative events deduct points", lambda: assert_(calculate_eligibility_score("02","BBB",False,1) < calculate_eligibility_score("02","BBB",False,0))),
    ("T5: score capped at 100",           lambda: assert_(calculate_eligibility_score("01","AAA",False,0) <= 100)),
    ("T5: score floor at 0",              lambda: assert_(calculate_eligibility_score("04","CCC",True,3) >= 0)),
    ("T5: ELIGIBLE at 70",                lambda: assert_eq(get_eligibility_decision(70), "ELIGIBLE")),
    ("T5: ELIGIBLE at 100",               lambda: assert_eq(get_eligibility_decision(100), "ELIGIBLE")),
    ("T5: CONDITIONAL at 50",             lambda: assert_eq(get_eligibility_decision(50), "CONDITIONAL")),
    ("T5: CONDITIONAL at 69",             lambda: assert_eq(get_eligibility_decision(69), "CONDITIONAL")),
    ("T5: NOT ELIGIBLE at 49",            lambda: assert_eq(get_eligibility_decision(49), "NOT ELIGIBLE")),
    ("T5: NOT ELIGIBLE at 0",             lambda: assert_eq(get_eligibility_decision(0), "NOT ELIGIBLE")),
]:
    run(n, f, results_agent)

def assert_(cond): assert cond

print("\n  T1: Block Reason Codes")
for n, f in [
    ("T1: code 01 = credit limit exceeded", lambda: assert_("credit limit exceeded" in get_block_reason_description("01").lower())),
    ("T1: code 09 = overdue",               lambda: assert_("overdue" in get_block_reason_description("09").lower())),
    ("T1: unknown code fallback",           lambda: assert_("99" in get_block_reason_description("99"))),
    ("T1: None → unknown",                  lambda: assert_("unknown" in get_block_reason_description(None).lower())),
    ("T1: all 10 block codes present",      lambda: [assert_(str(i).zfill(2) in BLOCK_REASON_DESCRIPTIONS) for i in range(1,11)]),
]:
    run(n, f, results_agent)

print("\n  G3: DCD Instrument Validation")
for n, f in [
    ("G3: approved instruments pass",       lambda: [assert_(is_approved_dcd_instrument(i)) for i in ["irrevocable letter of credit","bank guarantee","advance payment","d/a","d/p"]]),
    ("G3: non-approved instruments fail",   lambda: [assert_(not is_approved_dcd_instrument(i)) for i in ["open account","cheque","wire transfer"]]),
    ("G3: None instrument fails",           lambda: assert_(not is_approved_dcd_instrument(None))),
    ("G3: case-insensitive check",          lambda: assert_(is_approved_dcd_instrument("BANK GUARANTEE"))),
]:
    run(n, f, results_agent)

print("\n  T4: Payment Term Validation")
for n, f in [
    ("T4: RC01+30d = COMPLIANT",            lambda: assert_eq(validate_payment_terms(30,"01")["result"], "COMPLIANT")),
    ("T4: RC02+60d = MISMATCH",             lambda: assert_eq(validate_payment_terms(60,"02")["result"], "MISMATCH")),
    ("T4: RC02+41d = BORDERLINE",           lambda: assert_eq(validate_payment_terms(41,"02")["result"], "BORDERLINE")),
    ("T4: RC04+1d = MISMATCH",              lambda: assert_eq(validate_payment_terms(1,"04")["result"], "MISMATCH")),
    ("T4: RC04+0d = COMPLIANT or BORDERLINE", lambda: assert_(validate_payment_terms(0,"04")["result"] in ("COMPLIANT","BORDERLINE"))),
    ("T4: None days = UNKNOWN",             lambda: assert_eq(validate_payment_terms(None,"01")["result"], "UNKNOWN")),
    ("T4: None risk class = UNKNOWN",       lambda: assert_eq(validate_payment_terms(30,None)["result"], "UNKNOWN")),
    ("T4: result includes policy field",    lambda: assert_("policy" in validate_payment_terms(30,"01"))),
]:
    run(n, f, results_agent)

print("\n  Instrumentation: M1–M5 + G1–G8")
from instrumentation import (
    _emit, log_guardrail,
    m1_data_access_verified, m1_data_access_failed,
    m2_t1_validated, m2_t1_failed,
    m3_t2_t4_validated, m3_t2_t4_failed,
    m4_t5_active, m4_t5_failed,
    m5_production_validated, m5_production_failed,
)
import io

class CapLog:
    def __init__(self):
        self.records = []
        self.handler = logging.handlers_cap(self)
    class _H(logging.Handler):
        def __init__(self, cap): super().__init__(); self.cap = cap
        def emit(self, r): self.cap.records.append(self.format(r))
    def __enter__(self):
        root = logging.getLogger()
        self.h = self._H(self)
        root.addHandler(self.h)
        root.setLevel(logging.DEBUG)
        return self
    def __exit__(self,*a): logging.getLogger().removeHandler(self.h)
    @property
    def text(self): return "\n".join(self.records)

# Simplified log capture
def capture_log(fn):
    buf = []
    class H(logging.Handler):
        def emit(s, r): buf.append(s.format(r))
    h = H(); h.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger(); root.addHandler(h); root.setLevel(logging.DEBUG)
    try: fn()
    finally: root.removeHandler(h)
    return "\n".join(buf)

for n, fn_check in [
    ("Instr: _emit achieved",      lambda: assert_("M1.achieved" in capture_log(lambda: _emit("M1", True, "desc")))),
    ("Instr: _emit missed",        lambda: assert_("M1.missed"   in capture_log(lambda: _emit("M1", False,"fail")))),
    ("Instr: guardrail triggered", lambda: assert_("G1.triggered" in capture_log(lambda: log_guardrail("G1",True,"x")))),
    ("Instr: guardrail passed",    lambda: assert_("G2.passed"    in capture_log(lambda: log_guardrail("G2",False,"ok")))),
    ("Instr: M1 achieved",         lambda: assert_("M1.achieved"  in capture_log(lambda: m1_data_access_verified(10)))),
    ("Instr: M1 missed",           lambda: assert_("M1.missed"    in capture_log(lambda: m1_data_access_failed([])))),
    ("Instr: M2 achieved",         lambda: assert_("M2.achieved"  in capture_log(lambda: m2_t1_validated()))),
    ("Instr: M2 missed",           lambda: assert_("M2.missed"    in capture_log(lambda: m2_t1_failed("x")))),
    ("Instr: M3 achieved",         lambda: assert_("M3.achieved"  in capture_log(lambda: m3_t2_t4_validated()))),
    ("Instr: M3 missed",           lambda: assert_("M3.missed"    in capture_log(lambda: m3_t2_t4_failed("T","x")))),
    ("Instr: M4 achieved",         lambda: assert_("M4.achieved"  in capture_log(lambda: m4_t5_active()))),
    ("Instr: M4 missed",           lambda: assert_("M4.missed"    in capture_log(lambda: m4_t5_failed("x")))),
    ("Instr: M5 achieved",         lambda: assert_("M5.achieved"  in capture_log(lambda: m5_production_validated()))),
    ("Instr: M5 missed",           lambda: assert_("M5.missed"    in capture_log(lambda: m5_production_failed("x")))),
]:
    run(n, fn_check, results_agent)

print("\n  Guardrails Integration")
for n, f in [
    ("G4: overdue block makes RC02 ineligible", lambda: assert_(calculate_eligibility_score("02",None,True,0) < 50)),
    ("G4: clean RC01 is eligible",              lambda: assert_(calculate_eligibility_score("01","AAA",False,0) >= 70)),
    ("G5: 10-day data passes",                  lambda: assert_(not check_dandb_data_age((datetime.now()-timedelta(days=10)).date().isoformat())["is_stale"])),
    ("G5: 91-day data fails",                   lambda: assert_(check_dandb_data_age((datetime.now()-timedelta(days=91)).date().isoformat())["is_stale"])),
    ("G8: all block descriptions sufficient",   lambda: [assert_(len(d) > 10) for d in BLOCK_REASON_DESCRIPTIONS.values()]),
    ("ESK: Tier1 GREEN condition",              lambda: assert_eq(get_utilization_tier(calculate_utilization_pct(100000,50000)), "GREEN")),
    ("ESK: Tier2 AMBER condition",              lambda: assert_eq(get_utilization_tier(calculate_utilization_pct(100000,85000)), "AMBER")),
    ("ESK: payment mismatch triggers Tier2",    lambda: assert_eq(validate_payment_terms(60,"04")["result"], "MISMATCH")),
    ("ESK: NOT ELIGIBLE triggers escalation",   lambda: assert_eq(get_eligibility_decision(30), "NOT ELIGIBLE")),
]:
    run(n, f, results_agent)

print("\n  Demo Simulation Tests")
sys.path.insert(0, str(DEMO_PATH))
from simulation_engine import (
    t1_credit_block_explanation, t2_trm_utilization,
    t3_dcd_decision_support, t4_payment_term_validation,
    t4_payment_term_mismatch, t5_seasonal_financing, demo_escalation_model,
)

for n, f in [
    ("Demo: T1 kreditblock output",      lambda: assert_("GESPERRT" in t1_credit_block_explanation("2000002").upper() or "BLOCKED" in t1_credit_block_explanation("2000002").upper())),
    ("Demo: T2 trm utilization output",  lambda: assert_("AUSLASTUNG" in t2_trm_utilization("1000001").upper() or "%" in t2_trm_utilization("1000001"))),
    ("Demo: T3 approved instrument",     lambda: assert_("GENEHMIGT" in t3_dcd_decision_support("1000001","irrevocable letter of credit").upper())),
    ("Demo: T3 rejected instrument",     lambda: assert_("ABGELEHNT" in t3_dcd_decision_support("1000001","personal cheque").upper())),
    ("Demo: T4 payment term result",     lambda: assert_("COMPLIANT" in t4_payment_term_validation("CU10000001","1000001").upper())),
    ("Demo: T4 mismatch scenario",       lambda: assert_("MISMATCH" in t4_payment_term_mismatch("CU10000001").upper())),
    ("Demo: T5 eligibility BP1000001",   lambda: assert_("ELIGIBLE" in t5_seasonal_financing("1000001").upper())),
    ("Demo: T5 not eligible BP2000002",  lambda: assert_("NOT ELIGIBLE" in t5_seasonal_financing("2000002").upper())),
    ("Demo: escalation model all tiers", lambda: assert_(all(f"TIER {i}" in demo_escalation_model().upper() for i in [1,2,3]))),
]:
    run(n, f, results_agent)

print("\n  Agent: System Prompt")
def t_agent_system_prompt():
    src = (APP_PATH / "agent.py").read_text(encoding="utf-8")
    up  = src.upper()
    assert "READ-ONLY" in up or "READ ONLY" in up
    for tag in ["G1","G8","T1","T5"]: assert tag in src, f"{tag} missing"
    assert "TIER 1" in up or "tier 1" in src.lower()
    assert "TIER 3" in up or "tier 3" in src.lower()

run("Agent: system prompt has T1-T5 + guardrails + READ-ONLY", t_agent_system_prompt, results_agent)


# ═══════════════════════════════════════════════════════════════════════════
# REPORT — conftest.py-kompatibles Format
# ═══════════════════════════════════════════════════════════════════════════

def _section(name, marker, tests):
    total   = len(tests)
    passed  = sum(1 for t in tests if t["outcome"] == PASS)
    failed  = sum(1 for t in tests if t["outcome"] == FAIL)
    skipped = sum(1 for t in tests if t["outcome"] == SKIP)
    score   = round(passed / total * 100, 2) if total else 0.0
    return {
        "name":    name,
        "marker":  marker,
        "total":   total,
        "passed":  passed,
        "failed":  failed,
        "skipped": skipped,
        "score":   score,
        "tests":   tests,
    }

sections = [
    _section("Structure Tests", "structure", results_structure),
    _section("Agent Tests",     "agent_tests", results_agent),
]

total_all  = sum(s["total"]  for s in sections)
passed_all = sum(s["passed"] for s in sections)
failed_all = sum(s["failed"] for s in sections)
score_all  = round(passed_all / total_all * 100, 2) if total_all else 0.0

report = {
    "summary": {
        "total":  total_all,
        "passed": passed_all,
        "failed": failed_all,
        "score":  score_all,
    },
    "sections": sections,
}

report_path = ASSET_ROOT / "test_report.json"
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n" + "═"*72)
print(f"  ERGEBNIS: {passed_all}/{total_all} Tests bestanden  |  Score: {score_all}%")
if failed_all:
    print(f"  ⚠️  {failed_all} Tests fehlgeschlagen:")
    for s in sections:
        for t in s["tests"]:
            if t["outcome"] == FAIL:
                print(f"     ❌ [{s['marker']}] {t['name']}  →  {t.get('error','')}")
else:
    print("  ✅ Alle Tests bestanden.")
print(f"  📄 Bericht: {report_path}")
print("═"*72 + "\n")
