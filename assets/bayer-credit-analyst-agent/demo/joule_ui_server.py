"""
Bayer Credit Analyst Agent - Joule Demo UI Server
==================================================
Startet einen lokalen HTTP-Server mit einer vollstaendigen Joule-artigen
Chat-Oberflaeche fuer alle 100 Demo-Fragen.

Start:  python demo/joule_ui_server.py
Oeffne: http://localhost:8080
"""
import os, sys, json, threading, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

try:
    from simulation_engine import (
        t1_credit_block_explanation, t2_trm_utilization,
        t3_dcd_decision_support, t4_payment_term_validation,
        t4_payment_term_mismatch, t5_seasonal_financing,
        demo_escalation_model
    )
    from questions_100 import RAW_QUESTIONS
except Exception as e:
    print(f"[FEHLER] Import: {e}")
    sys.exit(1)

PORT = int(os.environ.get("JOULE_UI_PORT", "8080"))

# ─── Fragen mit Antwort-Funktion verknuepfen ──────────────────────────────────
def _fn(q):
    t, kw, qtext = q["task"], q["kw"], q["q"].lower()
    if t == "T1":
        return lambda: t1_credit_block_explanation(bp="2000002")
    if t == "T2":
        if "2000002" in kw or "2000002" in qtext:
            return lambda: t2_trm_utilization(bp="2000002")
        return lambda: t2_trm_utilization(bp="1000001")
    if t == "T3":
        bad = ["cheque","scheck","personal check","verboten","nicht zugelassen"]
        if any(b in qtext for b in bad) or "personal cheque" in kw:
            return lambda: t3_dcd_decision_support(bp="1000001", instrument="personal cheque")
        instr_map = {
            "bankgarantie dcd":"bank guarantee","bank guarantee dcd":"bank guarantee",
            "standby lc":"standby letter of credit","standby letter":"standby letter of credit",
            "documentary collection":"documentary collection","inkasso":"documentary collection",
            "vorauszahlung dcd":"advance payment","advance payment dcd":"advance payment",
            "bestaetigt akkreditiv":"confirmed letter of credit","confirmed lc":"confirmed letter of credit",
        }
        for key, instr in instr_map.items():
            if key in qtext or key in " ".join(kw):
                return (lambda i=instr: lambda: t3_dcd_decision_support(bp="1000001", instrument=i))()
        return lambda: t3_dcd_decision_support(bp="1000001", instrument="irrevocable letter of credit")
    if t == "T4":
        if any(x in qtext for x in ["60 tage","60 days","risikoklasse 04","mismatch"]) or "60 tage" in kw:
            return lambda: t4_payment_term_mismatch(customer="CU10000001")
        return lambda: t4_payment_term_validation(customer="CU10000001", bp="1000001")
    if t == "T5":
        if "2000002" in qtext or "2000002" in kw:
            return lambda: t5_seasonal_financing(bp="2000002")
        return lambda: t5_seasonal_financing(bp="1000001")
    return lambda: demo_escalation_model()

QUESTIONS = [{**q, "fn": _fn(q)} for q in RAW_QUESTIONS]

def match_question(text):
    tl = text.lower()
    best, bscore = None, 0
    for q in QUESTIONS:
        score = sum(1 for kw in q["kw"] if kw in tl)
        if score > bscore:
            bscore, best = score, q
    return best if bscore > 0 else None

def get_answer(query):
    query_l = query.lower().strip()
    # Direkter ID-Lookup
    try:
        num = int(query_l.replace("frage","").strip())
        qs = [q for q in QUESTIONS if q["id"] == num]
        if qs:
            try: return {"id": qs[0]["id"], "label": qs[0]["label"], "task": qs[0]["task"], "answer": qs[0]["fn"]()}
            except Exception as e: return {"error": str(e)}
    except ValueError:
        pass
    # Keyword-Matching
    m = match_question(query)
    if m:
        try: return {"id": m["id"], "label": m["label"], "task": m["task"], "answer": m["fn"]()}
        except Exception as e: return {"error": str(e)}
    return {"answer": None, "message": "Keine passende Demo-Frage gefunden. Bitte versuchen Sie einen anderen Begriff oder geben Sie eine Fragenummer (1-100) ein."}

# ─── HTML ─────────────────────────────────────────────────────────────────────
def build_html():
    qs_js = json.dumps([{"id":q["id"],"task":q["task"],"label":q["label"],"q":q["q"]} for q in QUESTIONS])
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bayer Credit Analyst Agent</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'72','72full',Arial,Helvetica,sans-serif;background:#f5f6f7;color:#32363a;height:100vh;display:flex;flex-direction:column}}
/* Header */
.header{{background:#0070f2;color:#fff;padding:0 24px;height:52px;display:flex;align-items:center;gap:12px;flex-shrink:0;box-shadow:0 2px 8px rgba(0,0,0,.2)}}
.header-logo{{width:32px;height:32px;background:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;color:#0070f2;font-size:14px}}
.header-title{{font-size:16px;font-weight:600}}
.header-subtitle{{font-size:12px;opacity:.8;margin-left:auto}}
.demo-badge{{background:#e8f4fd;color:#0070f2;border:1px solid #b0d4f1;border-radius:12px;padding:3px 10px;font-size:11px;font-weight:600}}
/* Layout */
.layout{{display:flex;flex:1;overflow:hidden}}
/* Sidebar */
.sidebar{{width:320px;background:#fff;border-right:1px solid #e4e6e8;display:flex;flex-direction:column;flex-shrink:0;overflow:hidden}}
.sidebar-header{{padding:12px 16px;border-bottom:1px solid #e4e6e8;background:#f7f8f9}}
.sidebar-title{{font-size:13px;font-weight:600;color:#32363a;margin-bottom:6px}}
.search-box{{width:100%;padding:7px 10px;border:1px solid #c7cbce;border-radius:6px;font-size:12px;outline:none;transition:border .2s}}
.search-box:focus{{border-color:#0070f2}}
.task-filter{{display:flex;gap:4px;margin-top:8px;flex-wrap:wrap}}
.task-btn{{padding:3px 8px;border:1px solid #c7cbce;border-radius:12px;font-size:11px;cursor:pointer;background:#fff;transition:all .2s}}
.task-btn.active,.task-btn:hover{{background:#0070f2;color:#fff;border-color:#0070f2}}
.q-list{{flex:1;overflow-y:auto;padding:4px 0}}
.q-item{{padding:10px 16px;cursor:pointer;border-bottom:1px solid #f0f1f2;transition:background .15s;display:flex;gap:8px;align-items:flex-start}}
.q-item:hover{{background:#e8f4fd}}
.q-item.active{{background:#daeeff;border-left:3px solid #0070f2}}
.q-badge{{background:#0070f2;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;white-space:nowrap;flex-shrink:0;margin-top:2px}}
.q-badge.T1{{background:#e53935}}.q-badge.T2{{background:#fb8c00}}.q-badge.T3{{background:#7b1fa2}}
.q-badge.T4{{background:#1565c0}}.q-badge.T5{{background:#2e7d32}}.q-badge.ESK{{background:#546e7a}}
.q-text{{font-size:12px;line-height:1.4;color:#32363a}}
.q-num{{font-size:10px;color:#8c9196;flex-shrink:0;width:26px;text-align:right;padding-top:2px}}
/* Main chat */
.main{{flex:1;display:flex;flex-direction:column;overflow:hidden}}
.chat-area{{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}}
/* Welcome */
.welcome{{text-align:center;padding:40px 20px;color:#566573}}
.welcome-icon{{font-size:48px;margin-bottom:12px}}
.welcome h2{{color:#0070f2;margin-bottom:8px;font-size:20px}}
.welcome p{{font-size:14px;line-height:1.6;max-width:480px;margin:0 auto 16px}}
.welcome-chips{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:560px;margin:0 auto}}
.chip{{padding:6px 14px;background:#e8f4fd;border:1px solid #b0d4f1;border-radius:16px;font-size:12px;cursor:pointer;transition:all .2s;color:#0070f2}}
.chip:hover{{background:#0070f2;color:#fff}}
/* Messages */
.msg{{display:flex;gap:10px;max-width:900px}}
.msg.user{{flex-direction:row-reverse;align-self:flex-end}}
.msg-avatar{{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0}}
.msg.agent .msg-avatar{{background:#0070f2;color:#fff}}
.msg.user .msg-avatar{{background:#e8f4fd;color:#0070f2}}
.msg-body{{max-width:820px}}
.msg-label{{font-size:11px;color:#8c9196;margin-bottom:4px}}
.msg.user .msg-label{{text-align:right}}
.bubble{{padding:12px 16px;border-radius:12px;font-size:13px;line-height:1.6}}
.msg.agent .bubble{{background:#fff;border:1px solid #e4e6e8;border-radius:2px 12px 12px 12px}}
.msg.user .bubble{{background:#0070f2;color:#fff;border-radius:12px 2px 12px 12px}}
.bubble pre{{font-family:monospace;white-space:pre-wrap;font-size:12px;margin:0;line-height:1.5}}
.bubble .task-tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-bottom:8px;color:#fff}}
.bubble .task-tag.T1{{background:#e53935}}.bubble .task-tag.T2{{background:#fb8c00}}
.bubble .task-tag.T3{{background:#7b1fa2}}.bubble .task-tag.T4{{background:#1565c0}}
.bubble .task-tag.T5{{background:#2e7d32}}.bubble .task-tag.ESK{{background:#546e7a}}
.bubble .q-label{{font-size:12px;color:#566573;margin-bottom:8px}}
/* Input */
.input-area{{padding:16px 20px;background:#fff;border-top:1px solid #e4e6e8;flex-shrink:0}}
.input-row{{display:flex;gap:8px;align-items:center}}
.input-box{{flex:1;padding:10px 14px;border:1px solid #c7cbce;border-radius:24px;font-size:13px;outline:none;transition:border .2s;font-family:inherit}}
.input-box:focus{{border-color:#0070f2;box-shadow:0 0 0 2px rgba(0,112,242,.15)}}
.send-btn{{width:40px;height:40px;border-radius:50%;background:#0070f2;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;flex-shrink:0}}
.send-btn:hover{{background:#0060d1}}
.send-btn svg{{width:18px;height:18px;fill:#fff}}
.hint{{font-size:11px;color:#8c9196;margin-top:6px;text-align:center}}
/* Loading */
.loading{{display:flex;gap:4px;padding:8px 0}}
.dot{{width:8px;height:8px;border-radius:50%;background:#0070f2;animation:bounce .8s infinite}}
.dot:nth-child(2){{animation-delay:.15s}}.dot:nth-child(3){{animation-delay:.3s}}
@keyframes bounce{{0%,80%,100%{{transform:scale(0)}}40%{{transform:scale(1)}}}}
.stats-bar{{padding:6px 20px;background:#f7f8f9;border-top:1px solid #e4e6e8;display:flex;gap:16px;font-size:11px;color:#8c9196}}
.stats-bar span{{color:#0070f2;font-weight:600}}
</style>
</head>
<body>
<div class="header">
  <div class="header-logo">B</div>
  <div class="header-title">Bayer Credit Analyst Agent</div>
  <div class="demo-badge">DEMO-MODUS</div>
  <div class="header-subtitle">100 simulierte Fragen · Read-Only · 8 Guardrails</div>
</div>
<div class="layout">
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">100 Demo-Fragen</div>
      <input class="search-box" id="search" placeholder="Suche..." oninput="filterQ()">
      <div class="task-filter">
        <button class="task-btn active" onclick="setFilter('ALL',this)">Alle</button>
        <button class="task-btn" onclick="setFilter('T1',this)" style="border-color:#e53935;color:#e53935">T1</button>
        <button class="task-btn" onclick="setFilter('T2',this)" style="border-color:#fb8c00;color:#fb8c00">T2</button>
        <button class="task-btn" onclick="setFilter('T3',this)" style="border-color:#7b1fa2;color:#7b1fa2">T3</button>
        <button class="task-btn" onclick="setFilter('T4',this)" style="border-color:#1565c0;color:#1565c0">T4</button>
        <button class="task-btn" onclick="setFilter('T5',this)" style="border-color:#2e7d32;color:#2e7d32">T5</button>
        <button class="task-btn" onclick="setFilter('ESK',this)" style="border-color:#546e7a;color:#546e7a">ESK</button>
      </div>
    </div>
    <div class="q-list" id="qlist"></div>
  </div>
  <!-- Main -->
  <div class="main">
    <div class="chat-area" id="chat">
      <div class="welcome" id="welcome">
        <div class="welcome-icon">🏦</div>
        <h2>Willkommen beim Bayer Credit Analyst Agent</h2>
        <p>Stellen Sie Fragen zu Kreditblocks, TRM-Auslastung, DCD-Instrumenten, Zahlungsbedingungen und saisonaler Finanzierung — oder waehlen Sie eine der 100 Demo-Fragen aus der Seitenleiste.</p>
        <div class="welcome-chips">
          <div class="chip" onclick="ask('Warum ist BP 2000002 gesperrt?')">🔴 Kreditblock BP 2000002</div>
          <div class="chip" onclick="ask('Akkreditiv fuer 1000001 zulaessig?')">📄 Akkreditiv pruefen</div>
          <div class="chip" onclick="ask('TRM Auslastung BP 1000001')">📊 TRM Auslastung</div>
          <div class="chip" onclick="ask('Zahlungsbedingungen CU10000001')">💳 Zahlungsbedingungen</div>
          <div class="chip" onclick="ask('Saisonale Finanzierung BP 1000001')">🌱 Saisonal Finanzierung</div>
          <div class="chip" onclick="ask('Alle 8 Guardrails erklaeren')">🛡️ Guardrails</div>
        </div>
      </div>
    </div>
    <div class="stats-bar">
      <span id="qcount">0</span> Fragen gestellt &nbsp;|&nbsp;
      Modell: <span>Simulation Engine</span> &nbsp;|&nbsp;
      LLM-Aufrufe: <span>0</span> (Read-Only Demo)
    </div>
    <div class="input-area">
      <div class="input-row">
        <input class="input-box" id="inp" placeholder="Frage eingeben oder Nummer 1-100..." onkeydown="if(event.key==='Enter')send()">
        <button class="send-btn" onclick="send()">
          <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="hint">Tipp: Geben Sie z.B. &quot;42&quot; fuer Frage 42 ein &nbsp;·&nbsp; &quot;alle&quot; laedt alle 100 Fragen</div>
    </div>
  </div>
</div>
<script>
const QUESTIONS = {qs_js};
let curFilter = 'ALL', qCount = 0;

function renderList(qs) {{
  const list = document.getElementById('qlist');
  list.innerHTML = '';
  qs.forEach(q => {{
    const el = document.createElement('div');
    el.className = 'q-item';
    el.id = 'qi-'+q.id;
    el.innerHTML = `<span class="q-num">${{q.id}}</span><span class="q-badge ${{q.task}}">${{q.task}}</span><span class="q-text">${{q.q}}</span>`;
    el.onclick = () => ask(q.q, q.id);
    list.appendChild(el);
  }});
}}

function filterQ() {{
  const s = document.getElementById('search').value.toLowerCase();
  const filtered = QUESTIONS.filter(q =>
    (curFilter === 'ALL' || q.task === curFilter) &&
    (q.q.toLowerCase().includes(s) || q.label.toLowerCase().includes(s) || String(q.id).includes(s))
  );
  renderList(filtered);
}}

function setFilter(f, btn) {{
  curFilter = f;
  document.querySelectorAll('.task-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterQ();
}}

function ask(text, id) {{
  document.getElementById('inp').value = text;
  document.querySelectorAll('.q-item').forEach(el => el.classList.remove('active'));
  if(id) {{ const el = document.getElementById('qi-'+id); if(el) {{ el.classList.add('active'); el.scrollIntoView({{block:'nearest'}}); }} }}
  send();
}}

function send() {{
  const inp = document.getElementById('inp');
  const text = inp.value.trim();
  if(!text) return;
  inp.value = '';
  const welcome = document.getElementById('welcome');
  if(welcome) welcome.remove();

  addMsg('user', text);
  const loadId = addLoading();

  fetch('/api/ask', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{query: text}})
  }})
  .then(r => r.json())
  .then(data => {{
    removeLoading(loadId);
    if(data.error) {{ addMsg('agent', '⛔ Fehler: ' + data.error); return; }}
    if(!data.answer) {{ addMsg('agent', data.message || 'Keine Antwort gefunden.'); return; }}
    addMsg('agent', data.answer, data.task, data.label, data.id);
    qCount++; document.getElementById('qcount').textContent = qCount;
  }})
  .catch(e => {{ removeLoading(loadId); addMsg('agent', '⛔ Verbindungsfehler: ' + e.message); }});
}}

let loadCount = 0;
function addLoading() {{
  const id = 'load-'+(++loadCount);
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.id = id; div.className = 'msg agent';
  div.innerHTML = `<div class="msg-avatar">B</div><div class="msg-body"><div class="bubble"><div class="loading"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div></div>`;
  chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
  return id;
}}
function removeLoading(id) {{ const el = document.getElementById(id); if(el) el.remove(); }}

function addMsg(role, text, task, label, id) {{
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  let content = '';
  if(role === 'agent') {{
    const tag = task ? `<span class="task-tag ${{task}}">${{task}}</span>` : '';
    const lbl = label ? `<div class="q-label">Frage ${{id||''}}: ${{label}}</div>` : '';
    content = `<div class="msg-avatar">B</div><div class="msg-body"><div class="msg-label">Bayer Credit Analyst Agent</div><div class="bubble">${{tag}}${{lbl}}<pre>${{escHtml(text)}}</pre></div></div>`;
  }} else {{
    content = `<div class="msg-body"><div class="msg-label" style="text-align:right">Sie</div><div class="bubble">${{escHtml(text)}}</div></div><div class="msg-avatar">U</div>`;
  }}
  div.innerHTML = content;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}}

function escHtml(t) {{ return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

// Initial render
renderList(QUESTIONS);
</script>
</body>
</html>"""

# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # Stille Logs

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = build_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/api/ask":
            length = int(self.headers.get("Content-Length",0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                result = get_answer(data.get("query",""))
            except Exception as e:
                result = {"error": str(e)}
            resp = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp)))
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

# ─── Start ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"""
========================================================================
  Bayer Credit Analyst Agent - Joule Demo UI
========================================================================
  URL:       {url}
  Fragen:    100 simulierte Demo-Fragen
  Modus:     Read-Only Simulation (kein LLM-Aufruf)
  Stoppen:   Ctrl+C
========================================================================
""")
    try:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server gestoppt.")
