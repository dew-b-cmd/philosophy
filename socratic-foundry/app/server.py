#!/usr/bin/env python3
"""
Socratic Foundry — 로컬 인터랙티브 인터뷰 서버 (stdlib 전용, 설치 불필요)

역할: state.json 을 단일 진실 소스로 삼아 각 게이트 화면(계약→가치→장면→경제성→암묵지→그래프→
역량→고객→논박→재정의→취약점→포트폴리오→검증→산출물)을 HTML 로 렌더링하고, 사용자의
입력·버튼을 state.pendingAction 으로 기록한다. 질문 생성·암묵지 분해·논박·기회 설계는
메인 Claude 가 한다(이 서버는 렌더링 + 이벤트 캡처만 — 뉴로심볼릭 분리의 심볼릭 층).
계약: references/session-protocol.md (SSOT)

사용법:  python3 server.py <session_dir> [port]
표준출력 첫 줄:  SF_SERVER_READY <url>
"""

import sys, os, json, html, socket, tempfile, threading, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse, unquote

SESSION_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
REQ_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8930
STATE_PATH = os.path.join(SESSION_DIR, "state.json")
_LOCK = threading.Lock()

# ---------- phase 카탈로그 ----------
PHASE_META = {
    "contract":   ("인터뷰 계약",   "GATE 0"),
    "values":     ("가치와 방향",   "GATE 1"),
    "scenes":     ("문제 장면",     "GATE 2"),
    "economics":  ("고통의 경제성", "GATE 3"),
    "mining":     ("암묵지 채굴",   "GATE 4"),
    "graph":      ("지식그래프",    "GATE 5"),
    "capability": ("역량과 자원",   "GATE 6"),
    "customers":  ("고객과 구매자", "GATE 7"),
    "elenchus":   ("소크라테스 논박", "GATE 8"),
    "reframe":    ("문제 재정의",   "GATE 9"),
    "audit":      ("취약점 감사",   "GATE 10"),
    "portfolio":  ("기회 포트폴리오", "GATE 11"),
    "validation": ("검증 실험",     "VALID"),
    "report":     ("최종 산출물",   "OUT"),
}

INTERVIEW_PHASES = {"values", "scenes", "economics", "mining", "customers", "elenchus", "audit"}

INTERVIEW_META = {
    "values": {
        "sub": "무엇을 만들 것인지보다, 왜 만들려는지를 먼저 알아냅니다.",
        "thesis": "돈·자율성·안정성·영향력·성장 — 무엇이 중요한지에 따라 같은 문제도 다른 사업이 됩니다. "
                  "원하지 않는 사업 방식(금지 조건)도 여기서 정합니다.",
        "advance": "가치 기준 정리하기 →",
    },
    "scenes": {
        "sub": "막연한 불편을 실제 사건으로 변환합니다. 진술보다 사건을 신뢰합니다.",
        "thesis": "“보고서 작성이 힘듭니다”는 약한 증거입니다. “매주 금요일 오후 3시, 여섯 개 지점 파일을 "
                  "합치는 데 3시간”은 강한 증거입니다. 최소 두 개의 실제 사건이 필요합니다.",
        "advance": "사건 정리하고 다음으로 →",
    },
    "economics": {
        "sub": "단순한 불편과 사업 가치가 있는 문제를 구분합니다.",
        "thesis": "빈도 × 시간 × 비용 × 오류 × 기회 손실. 문제가 사라진다면 무엇을 더 할 수 있는지까지 "
                  "물어야 ‘가장 비싼 문제’가 드러납니다.",
        "advance": "고통의 경제성 정리하기 →",
    },
    "mining": {
        "sub": "당연하게 여겨 설명하지 못한 판단 능력을 발굴합니다.",
        "thesis": "“감으로 안다”는 말 속에 판단 규칙이 있습니다. 규칙 · 신호 · 실제 사례 · 예외 — "
                  "최소 세 개의 판단 규칙과 각각의 사례가 확보되어야 합니다.",
        "advance": "판단 규칙 정리하기 →",
    },
    "customers": {
        "sub": "문제를 겪는 사람과 돈을 내는 사람을 분리합니다.",
        "thesis": "가장 아픈 사람과 결제하는 사람이 같은가? 누가 도입을 승인하고, 누구의 일이 늘어나고, "
                  "누가 기존 방식으로 이익을 보는가?",
        "advance": "이해관계자 정리하기 →",
    },
    "elenchus": {
        "sub": "핵심 주장마다 정의 · 일관성 · 근거 · 대안 · 귀결을 검토합니다.",
        "thesis": "AI 가 낸 그럴듯한 답도, 당신의 확신도 그대로 통과하지 않습니다. "
                  "살아남은 주장만 기획에 들어갑니다.",
        "advance": "논박 마치고 다음으로 →",
    },
    "audit": {
        "sub": "사업이나 실행을 실패시킬 가능성이 가장 큰 약점을 찾습니다.",
        "thesis": "“이 사업이 실패한다면 가장 가능성 높은 이유는?” — 아직 검증하지 않은 "
                  "가장 위험한 전제를 여기서 지목합니다.",
        "advance": "취약점 정리하기 →",
    },
}

MODES = [
    ("quick", "Quick Scan", "10~15분", "핵심 문제·자산 후보 + 추천 사업 형태 2~3개 + 추가 탐색 질문"),
    ("standard", "Standard Discovery", "30~45분", "문제 구조 + 도메인 지도 + 고객·구매자 + 기회 포트폴리오 + 7일 검증 실험"),
    ("deep", "Deep Mining", "60~90분+", "경력 전반 암묵지 + 지식그래프 + 논박 + 취약점 감사 + 30·90일 실행 계획"),
    ("challenge", "Idea Challenge", "30~60분", "이미 있는 아이디어를 논박·재정의합니다. 전제를 의심하는 모드"),
    ("productize", "Domain Productization", "40~60분", "전문가의 지식·컨설팅·강의·업무 방식을 상품으로 변환"),
]
MODE_LABEL = {m[0]: m[1] for m in MODES}

GOAL_TYPES = [
    ("problem_discovery", "문제 발굴", "내가 어떤 문제를 풀어야 할지부터 찾고 싶다"),
    ("idea_validation", "아이디어 검증", "이미 아이디어가 있고, 그 전제를 검증하고 싶다"),
    ("productization", "상품화", "내 경험·지식을 팔 수 있는 형태로 바꾸고 싶다"),
]

GATE_STATUS_LABEL = {"pending": "대기", "insufficient": "추가 필요", "sufficient": "충분", "passed": "완료"}
GATE_STATUS_CLS = {"pending": "gs-pend", "insufficient": "gs-insuf", "sufficient": "gs-suff", "passed": "gs-pass"}

NODE_STATUS_LABEL = {
    "proposed": "제안됨", "confirmed": "확인됨", "partial": "일부만",
    "needs_evidence": "근거 부족", "has_exception": "예외 있음", "explore_deeper": "더 깊게",
}
NODE_FEEDBACK = [
    ("confirmed", "맞습니다"), ("partial", "일부만 맞습니다"), ("needs_evidence", "근거가 부족합니다"),
    ("has_exception", "예외가 있습니다"), ("explore_deeper", "더 깊게 질문해 주세요"),
]

HORIZON_LABEL = {
    "now": "지금 바로 팔 수 있는 것", "product": "표준 상품형", "automation": "자동화형",
    "scale": "확장형", "option": "장기 옵션형",
}
GRADE_HINT = {
    "A": "실제 결제·반복 사용 확인", "B": "실제 문제·반복 행동 확인",
    "C": "사례·인터뷰 있음, 지불 미확인", "D": "사용자 추정 또는 AI 가설", "E": "근거 없음",
}
BOUNDARY_LABEL = {
    "ai_only": "AI 단독 수행", "ai_draft_human_review": "AI 수행 후 인간 검수",
    "human_decide_ai_execute": "인간 판단 후 AI 실행", "co_work": "인간·AI 공동 수행",
    "human_only": "인간만 수행", "automation_forbidden": "자동화 금지",
}


# ---------- state I/O ----------
def default_state():
    return {
        "version": 1, "phase": "contract", "phases": [], "processing": False,
        "notice": "", "pendingAction": None,
        "session": {"title": "", "mode": "", "purpose": "", "goalType": "",
                    "depthConsent": "", "offLimits": "", "desiredDecision": "",
                    "initialStatement": "", "status": "interviewing"},
        "thread": [], "currentQuestion": None,
        "ledger": {"facts": [], "inferences": [], "hypotheses": [], "contradictions": [], "gaps": []},
        "abstractions": [], "decisions": [],
        "values": {"workStyle": "", "priorities": [], "antiGoals": [],
                   "customerDepth": "", "teamPreference": "", "successMinimum": ""},
        "events": [], "pains": [], "judgmentRules": [], "assets": [],
        "graph": {"nodes": [], "edges": []},
        "capabilities": [],
        "stakeholders": {"problemHaver": "", "user": "", "beneficiary": "", "buyer": "",
                         "approver": "", "operator": "", "dataProvider": "", "blocker": "",
                         "buyerIsSufferer": None, "statusQuoWinner": "", "accessPath": "",
                         "firstCustomer": ""},
        "claims": [],
        "reframe": {"initialStatement": "", "observedProblem": "", "deeperProblem": "",
                    "opportunityStatement": "", "userVerdict": None},
        "vulnerabilities": [], "opportunities": [], "boundary": [], "experiments": [],
        "gates": {}, "gateReport": "", "reportPath": "",
    }


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            s = json.load(f)
        base = default_state()
        base.update(s)
        for k, dv in default_state().items():
            if isinstance(dv, dict) and isinstance(base.get(k), dict):
                merged = dict(dv); merged.update(base[k]); base[k] = merged
        return base
    except (FileNotFoundError, json.JSONDecodeError):
        s = default_state(); save_state(s); return s


def save_state(s):
    fd, tmp = tempfile.mkstemp(dir=SESSION_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def mutate(fn):
    with _LOCK:
        s = load_state(); fn(s); save_state(s); return s


# ---------- helpers ----------
def e(x):
    return html.escape("" if x is None else str(x))


def nl2br(x):
    return e(x).replace("\n", "<br>")


def badge(text, cls="bd"):
    return f'<span class="bd {cls}">{e(text)}</span>'


def score_dots(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    return "".join('<span class="dot-s %s"></span>' % ("on" if i < n else "") for i in range(5))


# ---------- 디자인 (knowledge-metabolism 사용설명서 토큰 계승) ----------
CSS = """
:root{
  --bg:#FBF8F2;--surface:#FFFFFF;--surface-2:#F4EEE2;
  --ink:#211C16;--ink-soft:#6A6051;--ink-faint:#9A8F7C;
  --line:#E9E0CF;--line-strong:#D8CCB4;
  --accent:#C2410C;--accent-deep:#9A3412;--accent-soft:#FBEADD;
  --sprout:#2F7D4F;--sprout-soft:#E3F0E6;
  --gold:#B45309;--gold-soft:#FBF0DA;
  --blue:#2C5E8A;--blue-soft:#E4EEF6;
  --violet:#6D5A9A;--violet-soft:#EDE9F5;
  --danger:#B4231E;--danger-soft:#F9E3E1;
  --code-bg:#272019;--code-ink:#EFE6D6;--code-accent:#E9A36B;
  --radius:14px;--radius-sm:9px;
  --shadow:0 1px 2px rgba(40,30,15,.04),0 8px 28px rgba(40,30,15,.06);
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"Pretendard","Pretendard Variable",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
font-size:15.5px;line-height:1.68;letter-spacing:-0.003em;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}
code{font-family:var(--mono)}
.app{display:grid;grid-template-columns:270px minmax(0,1fr) 330px;min-height:100vh}

/* ---- 좌측: 다크 레일 (게이트 + 도메인 맵) ---- */
.rail{background:linear-gradient(180deg,#2A231B 0%,#1F1913 100%);color:#E7DCC9;
padding:26px 20px 40px;position:sticky;top:0;height:100vh;overflow:auto;
border-right:1px solid rgba(0,0,0,.2)}
.rail::-webkit-scrollbar{width:8px}
.rail::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:8px}
.brand{display:flex;align-items:center;gap:11px;margin-bottom:6px}
.brand .glyph{width:38px;height:38px;border-radius:11px;flex:0 0 38px;
background:linear-gradient(135deg,var(--accent),var(--gold));display:grid;place-items:center;
font-size:19px;box-shadow:0 4px 14px rgba(194,65,12,.4)}
.brand .t1{font-weight:800;font-size:15.5px;color:#FFF8EC;line-height:1.2}
.brand .t2{font-size:11px;color:#B6A88E;font-family:var(--mono)}
.side-tag{margin:16px 0 18px;font-size:12px;color:#C9BBA1;line-height:1.55;
padding:10px 12px;background:rgba(255,255,255,.05);border-radius:10px;border:1px solid rgba(255,255,255,.07)}
.nav-label{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#8C7E66;
margin:20px 0 8px;font-weight:700}
.gate-list{list-style:none;margin:0;padding:0}
.gate-list li{position:relative;margin:0;padding:0 0 0 24px}
.gate-list li .gdot{position:absolute;left:3px;top:12px;width:9px;height:9px;border-radius:50%;
background:#57493A;border:2px solid #2A231B}
.gate-list li:not(:last-child)::before{content:"";position:absolute;left:6.5px;top:20px;bottom:-4px;
width:2px;background:#3B3126}
.gate-list li.done .gdot{background:var(--sprout)}
.gate-list li.cur .gdot{background:var(--accent);box-shadow:0 0 0 4px rgba(194,65,12,.25)}
.gate-list .grow{display:flex;align-items:center;gap:7px;padding:6px 0;font-size:13px;color:#B9AC93}
.gate-list li.done .grow{color:#D8CBB5}
.gate-list li.cur .grow{color:#FFD9BE;font-weight:700}
.gate-list .gnum{font-family:var(--mono);font-size:9.5px;color:#8C7E66;width:44px;flex:0 0 44px}
.gate-list li.cur .gnum{color:var(--code-accent)}
.gate-list button.gnav{all:unset;cursor:pointer;display:flex;align-items:center;gap:7px;width:100%}
.gate-list button.gnav:hover{color:#FFF3E0}
.gs{font-size:9.5px;font-family:var(--mono);font-weight:700;padding:1px 7px;border-radius:100px;
margin-left:auto;letter-spacing:.02em;white-space:nowrap}
.gs-pend{background:rgba(255,255,255,.07);color:#8C7E66}
.gs-insuf{background:rgba(180,35,30,.25);color:#F0A9A0}
.gs-suff{background:rgba(180,83,9,.28);color:#F0C98A}
.gs-pass{background:rgba(47,125,79,.3);color:#9ED2AE}
.dmap{margin-top:8px;font-size:12.5px}
.dmap .drow{display:flex;justify-content:space-between;padding:5px 2px;border-bottom:1px solid rgba(255,255,255,.06);color:#C9BBA1}
.dmap .drow b{color:#FFE9D2;font-family:var(--mono);font-weight:600}
.rail .foot{margin-top:26px;font-size:11px;color:#8C7E66;border-top:1px solid rgba(255,255,255,.08);padding-top:12px;line-height:1.7}

/* ---- 중앙 ---- */
.main{padding:40px 44px 120px;max-width:820px;margin:0 auto;width:100%;min-width:0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11.5px;
color:var(--accent-deep);background:var(--accent-soft);border:1px solid #F3D4BE;
padding:4px 11px;border-radius:100px;margin-bottom:14px;font-weight:600}
h1{font-size:27px;line-height:1.18;margin:0 0 8px;font-weight:850;letter-spacing:-0.02em}
h2{font-size:19px;margin:30px 0 12px;font-weight:800;letter-spacing:-0.015em}
h3{font-size:16px;margin:0 0 5px;font-weight:750}
.sub{color:var(--ink-soft);font-size:14.5px;margin:0 0 8px;max-width:640px}
.thesis{border-radius:var(--radius);padding:14px 18px;margin:16px 0 24px;font-size:14px;
line-height:1.62;background:linear-gradient(90deg,var(--gold-soft),var(--surface) 22%);
border:1px solid var(--line);border-left:4px solid var(--gold);color:#4a4238;box-shadow:var(--shadow)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
padding:18px 20px;margin:13px 0;box-shadow:var(--shadow)}
.card h3{margin:0 0 6px}
.hint{color:var(--ink-faint);font-size:12.5px;margin:2px 0 10px;line-height:1.55}
textarea{width:100%;min-height:110px;border:1px solid var(--line-strong);border-radius:10px;
padding:12px 14px;font:inherit;font-size:14.5px;resize:vertical;background:#fff;color:var(--ink)}
textarea.short{min-height:64px}
textarea:focus,input:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
input[type=text],select{width:100%;padding:10px 12px;border:1px solid var(--line-strong);
border-radius:10px;font:inherit;font-size:14.5px;background:#fff;color:var(--ink)}
label{display:block;font-weight:700;font-size:13px;margin:14px 0 5px;letter-spacing:-0.01em}
label.inline{font-weight:500;margin:6px 0;display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-size:14px}
.row{display:flex;gap:14px;flex-wrap:wrap}.row>div{flex:1;min-width:190px}
button{font:inherit;font-weight:700;border:0;border-radius:10px;padding:11px 18px;cursor:pointer;
background:var(--accent);color:#fff;font-size:14px;transition:filter .12s;letter-spacing:-0.01em}
button:hover{filter:brightness(1.07)}button:active{filter:brightness(.94)}
button.ghost{background:var(--surface-2);color:#5a5142;border:1px solid var(--line)}
button.line{background:#fff;border:1px solid var(--line-strong);color:var(--accent-deep)}
button.gold{background:var(--gold)}
button.green{background:var(--sprout)}
button.small{padding:7px 12px;font-size:12.5px}
button:disabled{opacity:.45;cursor:not-allowed}
.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px;align-items:center}
.bd{display:inline-block;font-size:10.5px;font-family:var(--mono);font-weight:700;
padding:2px 9px;border-radius:100px;margin:0 5px 4px 0;letter-spacing:.02em;
background:var(--surface-2);color:var(--ink-soft);border:1px solid var(--line-strong)}
.bd.acc{background:var(--accent-soft);color:var(--accent-deep);border-color:#F3D4BE}
.bd.gold{background:var(--gold-soft);color:var(--gold);border-color:#EBD7A8}
.bd.green{background:var(--sprout-soft);color:var(--sprout);border-color:#BEDDC8}
.bd.blue{background:var(--blue-soft);color:var(--blue);border-color:#C4D8E8}
.bd.violet{background:var(--violet-soft);color:var(--violet);border-color:#D5CCE8}
.bd.danger{background:var(--danger-soft);color:var(--danger);border-color:#EDBEBA}
.dot-s{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--line-strong);margin-right:3px}
.dot-s.on{background:var(--gold)}

/* 대화 스레드 */
.thread{margin:8px 0 20px}
.msg{margin:12px 0;max-width:94%}
.msg .who{font-size:11px;color:var(--ink-faint);font-weight:700;margin:0 0 3px;letter-spacing:.03em;font-family:var(--mono)}
.msg .bubble{padding:12px 16px;border-radius:13px;font-size:14.5px;white-space:pre-wrap;line-height:1.62}
.msg.interviewer .bubble{background:var(--surface);border:1px solid var(--line);border-top-left-radius:4px;box-shadow:var(--shadow)}
.msg.user{margin-left:auto}
.msg.user .who{text-align:right}
.msg.user .bubble{background:var(--blue-soft);border:1px solid #C4D8E8;border-top-right-radius:4px}
.msg.summary .bubble{background:var(--gold-soft);border:1px solid #EBD7A8;color:#6b5028;border-radius:11px}
.qcard{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);
border-radius:0 var(--radius) var(--radius) 0;padding:17px 19px;margin:18px 0 12px;box-shadow:var(--shadow)}
.qcard .q{font-size:16.5px;font-weight:750;margin:0 0 5px;line-height:1.45}
.qcard .why{font-size:12.5px;color:var(--ink-faint);margin:0 0 4px}
.qcard .why b{color:var(--gold);font-weight:700}
.opts{display:flex;flex-direction:column;gap:8px;margin:13px 0 4px}
.opts button,.opts label.opt{background:#fff;border:1px solid var(--line-strong);color:var(--ink);
text-align:left;font-weight:600;padding:11px 14px;border-radius:10px;font-size:14px;width:100%}
.opts button:hover{border-color:var(--accent);background:#FFFBF6}
.opts .ohint{display:block;font-size:12px;color:var(--ink-faint);font-weight:400;margin-top:2px}
.opts label.opt{display:flex;gap:10px;cursor:pointer;align-items:flex-start}

/* ---- 우측: Evidence Panel ---- */
.evid{background:var(--surface-2);border-left:1px solid var(--line);padding:26px 20px 40px;
position:sticky;top:0;height:100vh;overflow:auto}
.evid::-webkit-scrollbar{width:8px}
.evid::-webkit-scrollbar-thumb{background:var(--line-strong);border-radius:8px}
.evid h2{font-size:14px;margin:0 0 3px;font-weight:800}
.evid .esub{font-size:11.5px;color:var(--ink-faint);margin:0 0 16px}
.egroup{margin:0 0 16px}
.egroup .eh{font-size:11.5px;font-weight:800;letter-spacing:.04em;margin:0 0 6px;
display:flex;align-items:center;gap:7px;font-family:var(--mono)}
.egroup .eh .cnt{color:var(--ink-faint);font-weight:500}
.pip{width:9px;height:9px;border-radius:3px;flex:none}
.pip.fact{background:var(--sprout)}.pip.infer{background:var(--blue)}
.pip.hypo{background:var(--gold)}.pip.contra{background:var(--danger)}.pip.gap{background:var(--violet)}
.egroup ul{list-style:none;margin:0;padding:0}
.egroup li{font-size:12.5px;color:#4a4438;padding:4px 0 4px 11px;border-left:2px solid var(--line-strong);
margin:0 0 4px;line-height:1.5;background:none}
.egroup li .eid{font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-right:4px}
.egroup li.contra{border-left-color:var(--danger)}
.eempty{font-size:11.5px;color:var(--ink-faint);font-style:italic}
.abst{background:var(--danger-soft);border:1px solid #EDBEBA;border-radius:9px;padding:8px 11px;
font-size:12px;color:#7a2c28;margin:0 0 14px;line-height:1.5}

/* 그래프 트리 */
.gnode{border:1px solid var(--line);border-radius:var(--radius-sm);background:var(--surface);
padding:12px 15px;margin:8px 0;box-shadow:var(--shadow)}
.gnode .gtitle{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-weight:750;font-size:14.5px}
.gnode .gdetail{font-size:13px;color:var(--ink-soft);margin:4px 0 0;line-height:1.55}
.gnode .fb{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.gnode .fb button{padding:5px 10px;font-size:11.5px;background:#fff;border:1px solid var(--line-strong);
color:var(--ink-soft);font-weight:600;border-radius:8px}
.gnode .fb button:hover{border-color:var(--accent);color:var(--accent-deep)}
.gnode .fb input[type=text]{flex:1;min-width:140px;padding:5px 10px;font-size:12px;border-radius:8px}
.glvl1{margin-left:26px}.glvl2{margin-left:52px}.glvl3{margin-left:78px}

/* 기회 카드 */
.opp{position:relative;overflow:hidden}
.opp .obar{position:absolute;top:0;left:0;width:100%;height:3px;background:var(--accent)}
.opp.h-now .obar{background:var(--sprout)}.opp.h-product .obar{background:var(--gold)}
.opp.h-automation .obar{background:var(--blue)}.opp.h-scale .obar{background:var(--accent)}
.opp.h-option .obar{background:var(--violet)}
.opp .score-row{display:flex;gap:20px;flex-wrap:wrap;margin:9px 0 4px;font-size:12.5px;color:var(--ink-soft)}
.opp .score-row .sc b{font-family:var(--mono);color:var(--ink)}
.grade{font-family:var(--mono);font-weight:800;font-size:13px;width:26px;height:26px;border-radius:8px;
display:inline-grid;place-items:center;margin-right:6px}
.grade.gA{background:var(--sprout-soft);color:var(--sprout)}
.grade.gB{background:#E9F2E4;color:#4E7D3A}
.grade.gC{background:var(--gold-soft);color:var(--gold)}
.grade.gD{background:var(--accent-soft);color:var(--accent-deep)}
.grade.gE{background:var(--danger-soft);color:var(--danger)}
.kv{font-size:13px;color:var(--ink-soft);margin:3px 0}
.kv b{color:var(--ink);font-weight:700}

/* 표 */
.tblw{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--surface)}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--surface-2);font-weight:750;font-size:12px;white-space:nowrap}
tr:last-child td{border-bottom:none}

.foot{color:var(--ink-faint);font-size:12px;margin-top:32px;border-top:1px solid var(--line);padding-top:13px;line-height:1.7}
#banner{position:fixed;top:0;left:0;right:0;background:var(--accent);color:#fff;text-align:center;
padding:9px;font-size:13px;font-weight:700;display:none;z-index:99}
@media(max-width:1180px){.app{grid-template-columns:230px minmax(0,1fr)}.evid{display:none}}
@media(max-width:860px){.app{grid-template-columns:1fr}.rail{position:static;height:auto}
.main{padding:28px 20px 90px}}
"""

POLL_JS = """
let _v=%VER%;
async function poll(){
 try{const r=await fetch('/state',{cache:'no-store'});const s=await r.json();
  if(s.version!==_v){location.reload();return;}
  const b=document.getElementById('banner');
  if(b){if(s.processing){b.textContent=s.notice||'생각을 벼리고 있습니다… 잠시만 기다려주세요.';
    b.style.display='block';document.querySelectorAll('button,textarea,input,select').forEach(x=>x.disabled=true);}
   else{b.style.display='none';}}
 }catch(_){}
}
setInterval(poll,1500);
"""


# ---------- 좌측 레일 ----------
def rail_html(state):
    phases = state.get("phases") or []
    cur = state.get("phase", "contract")
    if not phases:
        phases = ["contract"]
    try:
        cur_i = phases.index(cur)
    except ValueError:
        cur_i = 0
    gates = state.get("gates", {}) or {}
    items = ""
    for i, p in enumerate(phases):
        label, gnum = PHASE_META.get(p, (p, ""))
        cls = []
        if i < cur_i:
            cls.append("done")
        if p == cur:
            cls.append("cur")
        st = gates.get(p, "pending")
        if p == cur and st == "pending":
            st_html = ""
        else:
            st_html = f'<span class="gs {GATE_STATUS_CLS.get(st,"gs-pend")}">{GATE_STATUS_LABEL.get(st,st)}</span>'
        inner = f'<span class="gnum">{e(gnum)}</span><span>{e(label)}</span>{st_html}'
        if i < cur_i:
            body = (f'<form method="post" action="/nav" style="margin:0">'
                    f'<input type="hidden" name="to" value="{p}">'
                    f'<button type="submit" class="gnav">{inner}</button></form>')
        else:
            body = f'<span class="grow">{inner}</span>'
        items += f'<li class="{" ".join(cls)}"><span class="gdot"></span>{body}</li>'

    dmap = ""
    counts = [
        ("실제 사건", len(state.get("events", []))),
        ("고통 지점", len(state.get("pains", []))),
        ("판단 규칙", len(state.get("judgmentRules", []))),
        ("비대칭 자산", len(state.get("assets", []))),
        ("그래프 노드", len((state.get("graph") or {}).get("nodes", []))),
        ("취약점", len(state.get("vulnerabilities", []))),
        ("기회 후보", len(state.get("opportunities", []))),
    ]
    for lab, n in counts:
        dmap += f'<div class="drow"><span>{e(lab)}</span><b>{n}</b></div>'

    mode = (state.get("session") or {}).get("mode", "")
    mode_tag = f' · {e(MODE_LABEL.get(mode, ""))}' if mode else ""
    return f"""<aside class="rail">
  <div class="brand"><div class="glyph">⚒</div>
    <div><div class="t1">소크라틱 파운드리</div><div class="t2">SOCRATIC FOUNDRY{mode_tag}</div></div></div>
  <div class="side-tag">무엇을 만들고 싶은지 묻는 데서 멈추지 않습니다.<br>
  당신이 <b>무엇을 만들어야 하는지</b> 함께 찾아냅니다.</div>
  <div class="nav-label">Interview Gates</div>
  <ul class="gate-list">{items}</ul>
  <div class="nav-label">Domain Map</div>
  <div class="dmap">{dmap}</div>
  <div class="foot">진술보다 사건 · 관심보다 전문성<br>효율보다 효과 · 모든 결론은 추적 가능</div>
</aside>"""


# ---------- 우측 Evidence Panel ----------
def evid_html(state):
    led = state.get("ledger", {}) or {}
    groups = [
        ("facts", "FACTS · 확인된 사실", "fact", "content"),
        ("inferences", "INFERENCES · AI 추론", "infer", "content"),
        ("hypotheses", "HYPOTHESES · 검증 필요", "hypo", "content"),
        ("contradictions", "CONTRADICTIONS · 모순", "contra", None),
        ("gaps", "GAPS · 지식 공백", "gap", None),
    ]
    blocks = ""
    for key, title, cls, field in groups:
        items = led.get(key, []) or []
        shown = items[-7:]
        li = ""
        for x in shown:
            if key == "contradictions" and isinstance(x, dict):
                mark = "✓ " if x.get("status") == "resolved" else ""
                li += (f'<li class="contra"><span class="eid">{e(x.get("id",""))}</span>'
                       f'{mark}{e(x.get("a",""))} ↔ {e(x.get("b",""))}</li>')
            elif isinstance(x, dict):
                li += f'<li><span class="eid">{e(x.get("id",""))}</span>{e(x.get(field or "content",""))}</li>'
            else:
                li += f'<li>{e(x)}</li>'
        if not li:
            li = '<li class="eempty" style="border:0;padding-left:0">아직 없음</li>'
        more = f' <span class="cnt">외 {len(items)-7}</span>' if len(items) > 7 else ""
        blocks += (f'<div class="egroup"><div class="eh"><span class="pip {cls}"></span>{e(title)}'
                   f' <span class="cnt">{len(items)}</span>{more}</div><ul>{li}</ul></div>')

    unresolved = [a for a in state.get("abstractions", []) if not a.get("resolved")]
    abst = ""
    if unresolved:
        terms = " · ".join(e(a.get("term", "")) for a in unresolved[-5:])
        abst = f'<div class="abst">⚠ 정의되지 않은 추상어: <b>{terms}</b><br>정의 전에는 통과되지 않습니다.</div>'

    return f"""<aside class="evid">
  <h2>Evidence Panel</h2>
  <p class="esub">사실 · 추론 · 가설을 절대 섞지 않습니다.</p>
  {abst}{blocks}
</aside>"""


def page(state, center, title="Socratic Foundry"):
    js = POLL_JS.replace("%VER%", str(state.get("version", 0)))
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><style>{CSS}</style></head><body>
<div id="banner"></div>
<div class="app">{rail_html(state)}<main class="main">{center}</main>{evid_html(state)}</div>
<script>{js}</script></body></html>"""


# ---------- 공용 컴포넌트 ----------
def phase_header(state, p):
    label, gnum = PHASE_META.get(p, (p, ""))
    meta = INTERVIEW_META.get(p, {})
    out = f'<div class="eyebrow">{e(gnum)} · {e(label)}</div>'
    title = (state.get("session") or {}).get("title", "")
    out += f'<h1>{e(label)}</h1>'
    if meta.get("sub"):
        out += f'<p class="sub">{e(meta["sub"])}</p>'
    if meta.get("thesis"):
        out += f'<div class="thesis">{e(meta["thesis"])}</div>'
    return out


def thread_html(state, phase):
    out = '<div class="thread">'
    for m in state.get("thread", []):
        if m.get("phase") and m.get("phase") != phase:
            continue
        role = m.get("role", "interviewer")
        kind = m.get("kind", "")
        cls = "summary" if kind == "summary" else ("user" if role == "user" else "interviewer")
        who = "나" if role == "user" else "파운드리"
        if kind == "summary":
            who = "파운드리 · 중간 요약"
        out += (f'<div class="msg {cls}"><div class="who">{who}</div>'
                f'<div class="bubble">{nl2br(m.get("content",""))}</div></div>')
    out += "</div>"
    return out


def question_form(state):
    q = state.get("currentQuestion")
    if not q:
        return ""
    why = f'<p class="why"><b>왜 묻는가</b> — {e(q["why"])}</p>' if q.get("why") else ""
    opts = ""
    if q.get("options"):
        if q.get("allowMulti"):
            chk = "".join(
                f'<label class="opt"><input type="checkbox" name="opt" value="{i}"> '
                f'<span><b>{e(o.get("label",""))}</b>'
                f'{("<span class=ohint>"+e(o.get("hint",""))+"</span>") if o.get("hint") else ""}</span></label>'
                for i, o in enumerate(q["options"]))
            opts = (f'<form method="post" action="/choose" class="opts">{chk}'
                    f'<div class="actions"><button type="submit">선택 확정 →</button></div></form>')
        else:
            btns = ""
            for o in q["options"]:
                hint = f'<span class="ohint">{e(o.get("hint",""))}</span>' if o.get("hint") else ""
                btns += (f'<form method="post" action="/answer" style="margin:0">'
                         f'<input type="hidden" name="text" value="{e(o.get("label",""))}">'
                         f'<button type="submit"><b>{e(o.get("label",""))}</b>{hint}</button></form>')
            opts = f'<div class="opts">{btns}</div>'
    ph = e(q.get("placeholder") or "여기에 답을 적으세요. 실제 있었던 장면을 그대로 적어도 좋습니다.")
    btns = '<button type="submit">답하기 →</button>'
    if q.get("allowExample", True):
        btns += '<button class="line" name="op" value="example" type="submit" formaction="/interview">예시 보기</button>'
    if q.get("allowUnsure", True):
        btns += '<button class="ghost" name="op" value="unsure" type="submit" formaction="/interview">잘 모르겠습니다</button>'
    if q.get("allowSkip", True):
        btns += '<button class="ghost" name="op" value="skip" type="submit" formaction="/interview">건너뛰기</button>'
    btns += '<button class="ghost" name="op" value="deeper" type="submit" formaction="/interview">더 깊게</button>'
    if len([m for m in state.get("thread", []) if m.get("role") == "user"]) >= 1:
        btns += '<button class="ghost" name="op" value="back" type="submit" formaction="/interview">이전 답변 수정</button>'
        btns += '<button class="ghost" name="op" value="summary" type="submit" formaction="/interview">중간 요약</button>'
    return f"""<div class="qcard"><p class="q">{e(q["text"])}</p>{why}{opts}</div>
<form method="post" action="/answer">
<textarea name="text" placeholder="{ph}"></textarea>
<div class="actions">{btns}</div></form>"""


# ---------- phase별 산출물 요약 카드 (interview 화면 하단) ----------
def summary_cards(state, phase):
    out = ""
    if phase == "values":
        v = state.get("values", {})
        if any([v.get("workStyle"), v.get("priorities"), v.get("antiGoals"), v.get("successMinimum")]):
            pri = " → ".join(e(x) for x in v.get("priorities", []))
            anti = " · ".join(e(x) for x in v.get("antiGoals", []))
            out += (f'<div class="card"><h3>지금까지 확정된 가치 기준</h3>'
                    f'<p class="kv"><b>일하는 방식</b> {e(v.get("workStyle","")) or "—"}</p>'
                    f'<p class="kv"><b>우선순위</b> {pri or "—"}</p>'
                    f'<p class="kv"><b>금지 조건</b> {anti or "—"}</p>'
                    f'<p class="kv"><b>성공 최소 조건</b> {e(v.get("successMinimum","")) or "—"}</p></div>')
    elif phase == "scenes":
        for ev in state.get("events", []):
            out += (f'<div class="card"><h3>{badge(ev.get("id",""),"bd acc")} {e(ev.get("title",""))}</h3>'
                    f'<p class="kv"><b>언제</b> {e(ev.get("when","")) or "—"} · <b>무엇을 하다가</b> {e(ev.get("doing","")) or "—"}</p>'
                    f'<p class="kv"><b>막힌 곳</b> {e(ev.get("stuckAt","")) or "—"} · <b>걸린 시간</b> {e(ev.get("timeTaken","")) or "—"}</p>'
                    f'<p class="kv"><b>임시방편</b> {e(ev.get("workaround","")) or "—"} · <b>포기한 것</b> {e(ev.get("gaveUp","")) or "—"}</p></div>')
        if out:
            out = "<h2>확보된 실제 사건</h2>" + out
    elif phase == "economics":
        rows = ""
        for p_ in state.get("pains", []):
            rows += (f'<tr><td>{e(p_.get("id",""))}</td><td>{e(p_.get("description",""))}</td>'
                     f'<td>월 {e(p_.get("frequencyPerMonth","?"))}회</td>'
                     f'<td>{e(p_.get("hoursPerOccurrence","?"))}h</td>'
                     f'<td>{e(p_.get("unlockedIfSolved","")) or "—"}</td></tr>')
        if rows:
            out = ('<h2>고통의 경제성</h2><div class="tblw"><table>'
                   '<tr><th>ID</th><th>문제</th><th>빈도</th><th>1회 시간</th><th>해결 시 얻는 것</th></tr>'
                   + rows + "</table></div>")
    elif phase == "mining":
        for r in state.get("judgmentRules", []):
            sig = " · ".join(e(x) for x in r.get("signals", []))
            exc = " · ".join(e(x) for x in r.get("exceptions", []))
            out += (f'<div class="card"><h3>{badge(r.get("id",""),"bd gold")} {e(r.get("rule",""))}</h3>'
                    f'<p class="kv"><b>신호</b> {sig or "—"}</p>'
                    f'<p class="kv"><b>실제 사례</b> {e(r.get("example","")) or "—"}</p>'
                    f'<p class="kv"><b>예외</b> {exc or "—"} · <b>초보자 실수</b> {e(r.get("noviceMistake","")) or "—"}</p></div>')
        if out:
            out = "<h2>발굴된 판단 규칙</h2>" + out
        acards = ""
        for a in state.get("assets", []):
            acards += (f'<div class="card"><h3>{badge(a.get("kind",""),"bd blue")} {e(a.get("description",""))}</h3>'
                       f'<p class="kv"><b>근거</b> {e(a.get("evidence","")) or "—"} · '
                       f'<b>복제 난이도</b> {e(a.get("replicability","")) or "—"}</p></div>')
        if acards:
            out += "<h2>비대칭 자산</h2>" + acards
    elif phase == "customers":
        st = state.get("stakeholders", {})
        if any(st.get(k) for k in ("problemHaver", "buyer", "user")):
            bis = st.get("buyerIsSufferer")
            bis_t = "같음" if bis is True else ("다름 ⚠" if bis is False else "미확인")
            out = (f'<div class="card"><h3>이해관계자 분리</h3>'
                   f'<p class="kv"><b>문제 경험자</b> {e(st.get("problemHaver","")) or "—"} · <b>실제 사용자</b> {e(st.get("user","")) or "—"}</p>'
                   f'<p class="kv"><b>구매자</b> {e(st.get("buyer","")) or "—"} · <b>승인자</b> {e(st.get("approver","")) or "—"}</p>'
                   f'<p class="kv"><b>도입 방해자</b> {e(st.get("blocker","")) or "—"} · <b>기존 방식 수혜자</b> {e(st.get("statusQuoWinner","")) or "—"}</p>'
                   f'<p class="kv"><b>아픈 사람 = 내는 사람?</b> {bis_t} · <b>첫 고객</b> {e(st.get("firstCustomer","")) or "—"}</p></div>')
    elif phase == "elenchus":
        for c in state.get("claims", []):
            checks = ""
            for ch in c.get("checks", []):
                v = ch.get("verdict", "")
                cls = {"pass": "green", "fail": "danger", "revised": "gold"}.get(v, "")
                checks += badge(f'{ch.get("kind","")}:{v or "…"}', f"bd {cls}")
            stat = {"open": "", "survived": badge("생존", "bd green"),
                    "revised": badge("수정됨", "bd gold"), "withdrawn": badge("철회", "bd danger")}.get(c.get("status", "open"), "")
            out += (f'<div class="card"><h3>{badge(c.get("id",""),"bd violet")} {e(c.get("claim",""))} {stat}</h3>'
                    f'<div>{checks}</div></div>')
        if out:
            out = "<h2>논박 중인 주장</h2>" + out
    elif phase == "audit":
        for v in state.get("vulnerabilities", []):
            sev = {"high": "danger", "mid": "gold", "low": ""}.get(v.get("severity", ""), "")
            risk = badge("가장 위험한 가설", "bd danger") if v.get("isRiskiestAssumption") else ""
            out += (f'<div class="card"><h3>{badge(v.get("category",""),"bd "+sev)} {e(v.get("description",""))} {risk}</h3>'
                    f'<p class="kv"><b>대응</b> {e(v.get("mitigation","")) or "—"}</p></div>')
        if out:
            out = "<h2>발견된 취약점</h2>" + out
    return out


# ---------- 화면: contract ----------
def render_contract(s):
    sess = s.get("session", {})
    mcards = ""
    for mid, name, dur, desc in MODES:
        mcards += (f'<label class="inline" style="border:1px solid var(--line);border-radius:11px;'
                   f'padding:12px 14px;margin:8px 0;background:#fff;box-shadow:var(--shadow)">'
                   f'<input type="radio" name="mode" value="{mid}" {"checked" if sess.get("mode")==mid else ""} required> '
                   f'<span><b>{e(name)}</b> <span class="bd">{e(dur)}</span>'
                   f'<span class="ohint" style="display:block;font-size:12.5px;color:var(--ink-faint)">{e(desc)}</span></span></label>')
    gcards = ""
    for gid, name, desc in GOAL_TYPES:
        gcards += (f'<label class="inline"><input type="radio" name="goalType" value="{gid}" '
                   f'{"checked" if sess.get("goalType")==gid else ""}> '
                   f'<span><b>{e(name)}</b> — <span style="color:var(--ink-faint);font-size:13px">{e(desc)}</span></span></label>')
    center = f"""
<div class="eyebrow">GATE 0 · 인터뷰 계약</div>
<h1>무엇을 만들어야 하는지,<br>함께 찾아냅니다</h1>
<p class="sub">아이디어를 곧바로 기획서로 바꾸지 않습니다. 당신의 경험·판단 기준·자산에서
문제를 발굴하고, 증거로 설명 가능한 사업 기회로 주조합니다.</p>
<div class="thesis">인터뷰의 범위·깊이·원하는 결과를 먼저 합의합니다. 여기서 승인한 계약이
이후 모든 질문의 경계가 됩니다.</div>
<form method="post" action="/start">
  <label>진행 모드</label>
  {mcards}
  <label>오늘 가장 알고 싶은 것은 무엇입니까?</label>
  <textarea class="short" name="purpose" placeholder="예: 퇴사 후 내 경험으로 무엇을 팔 수 있는지 / 이 SaaS 아이디어가 맞는 방향인지" required>{e(sess.get("purpose",""))}</textarea>
  <label>아이디어 검증 · 문제 발굴 · 상품화 — 어디에 가깝습니까?</label>
  {gcards}
  <label>지금 머릿속에 있는 생각을 자유롭게 적어주세요 (최초 진술)</label>
  <p class="hint">만들고 싶은 것, 반복되는 불편, 팔고 싶은 경험 — 완성된 문장이 아니어도 됩니다. 이 진술은 나중에 ‘재정의된 문제’와 나란히 비교됩니다.</p>
  <textarea name="initialStatement" placeholder="예: 병원 블로그 글을 자동으로 만들어 주는 서비스를 만들고 싶다" required>{e(sess.get("initialStatement",""))}</textarea>
  <div class="row">
    <div><label>어느 깊이까지 질문해도 괜찮습니까?</label>
      <select name="depthConsent">
        <option value="work">업무·경력까지</option>
        <option value="money">재정·수익 목표까지</option>
        <option value="all" selected>가치관·삶의 방향까지 모두</option>
      </select></div>
    <div><label>공개하기 불편한 영역 (선택)</label>
      <input type="text" name="offLimits" value="{e(sess.get("offLimits",""))}" placeholder="예: 이전 회사 내부 정보, 가족 관련"></div>
  </div>
  <label>인터뷰가 끝나면 어떤 결정을 내릴 수 있어야 합니까?</label>
  <input type="text" name="desiredDecision" value="{e(sess.get("desiredDecision",""))}" placeholder="예: 다음 달에 시작할 첫 실험 하나를 고른다" required>
  <div class="actions"><button type="submit">계약하고 인터뷰 시작 →</button></div>
</form>
<p class="foot">모든 데이터는 이 컴퓨터의 세션 폴더에만 저장됩니다. 개인적 상처를 마케팅 소재로 쓰지 않으며,
말하지 않은 전문성을 지어내지 않습니다.</p>"""
    return page(s, center)


# ---------- 화면: interview (공용) ----------
def render_interview(s):
    p = s.get("phase")
    meta = INTERVIEW_META.get(p, {})
    adv_label = meta.get("advance", "다음 단계로 →")
    adv = (f'<form method="post" action="/advance" style="margin-top:10px">'
           f'<button class="gold" type="submit">{e(adv_label)}</button>'
           f'<span class="hint" style="margin-left:10px">충분히 이야기했다면 파운드리가 이 게이트의 산출물을 정리합니다.</span></form>')
    center = phase_header(s, p) + thread_html(s, p) + question_form(s) + summary_cards(s, p) + adv
    return page(s, center)


# ---------- 화면: graph ----------
def render_graph(s):
    nodes = (s.get("graph") or {}).get("nodes", [])
    depth = {}
    by_id = {n.get("id"): n for n in nodes}

    def d_of(n, guard=0):
        if guard > 6:
            return 0
        pid = n.get("parentId")
        if not pid or pid not in by_id:
            return 0
        return 1 + d_of(by_id[pid], guard + 1)

    cards = ""
    for n in nodes:
        lvl = min(d_of(n), 3)
        st = n.get("status", "proposed")
        st_cls = {"confirmed": "green", "partial": "gold", "needs_evidence": "danger",
                  "has_exception": "violet", "explore_deeper": "blue"}.get(st, "")
        fb_btns = "".join(
            f'<button type="submit" name="verdict" value="{v}">{lab}</button>'
            for v, lab in NODE_FEEDBACK)
        cards += f"""<div class="gnode glvl{lvl}">
  <div class="gtitle">{badge(n.get("type",""),"bd blue")} {e(n.get("label",""))}
    {badge(NODE_STATUS_LABEL.get(st,st), "bd "+st_cls)}</div>
  {f'<p class="gdetail">{e(n.get("detail",""))}</p>' if n.get("detail") else ""}
  <form method="post" action="/graph-feedback" class="fb">
    <input type="hidden" name="nodeId" value="{e(n.get("id",""))}">
    {fb_btns}
    <input type="text" name="comment" placeholder="코멘트 (선택)">
  </form>
</div>"""
    if not cards:
        cards = '<p class="hint">파운드리가 지금까지의 발견으로 지식그래프를 그리고 있습니다…</p>'
    center = f"""
{phase_header(s, "graph")}
<p class="sub">지금까지 발견한 경험 · 문제 · 판단 신호 · 규칙 · 예외 · 자산 · 기회의 연결입니다.
각 노드에 피드백을 주세요 — <b>당신이 승인하지 않은 노드는 결론에 쓰이지 않습니다.</b></p>
<div class="thesis">‘맞습니다’만 고르라고 만든 화면이 아닙니다. 근거가 부족하거나 예외가 있으면
그렇게 표시하세요. 그 피드백이 다음 질문이 됩니다.</div>
{thread_html(s, "graph")}{question_form(s)}
{cards}
<form method="post" action="/graph-done" style="margin-top:16px">
  <button class="gold" type="submit">그래프 확인 완료 — 다음 게이트로 →</button>
</form>
<p class="foot">피드백을 줄 때마다 파운드리가 노드를 갱신하거나 더 깊은 질문으로 돌아옵니다.</p>"""
    return page(s, center)


# ---------- 화면: capability ----------
def render_capability(s):
    caps = s.get("capabilities", [])
    cards = ""
    for c in caps:
        cards += (f'<div class="card"><h3>{e(c.get("area",""))}</h3>'
                  f'<p style="font-size:14px;margin:4px 0">{e(c.get("assessment",""))}</p>'
                  f'<p class="kv"><b>근거</b> {e(c.get("evidence","")) or "—"}</p>'
                  f'<p class="kv"><b>공백</b> {e(c.get("gapNote","")) or "—"}</p></div>')
    if not cards:
        cards = '<p class="hint">파운드리가 인터뷰 내용으로 역량·자원 평가를 준비하고 있습니다…</p>'
    center = f"""
{phase_header(s, "capability")}
<p class="sub">초급·중급·고급 딱지가 아니라, 근거가 있는 서술로 평가합니다.
평가가 실제와 다르면 바로잡아 주세요 — 이 평가가 기회 포트폴리오의 ‘창업자 적합성’ 축이 됩니다.</p>
{cards}
<form method="post" action="/capability">
  <label>바로잡을 내용 (선택)</label>
  <textarea class="short" name="comment" placeholder="예: 판매 경험이 부족하다고 했지만, 사내에서 교육 프로그램을 3년간 팔아본 경험이 있습니다"></textarea>
  <div class="actions">
    <button class="line" name="op" value="fix" type="submit">수정 요청</button>
    <button class="gold" name="op" value="ok" type="submit">이 평가로 진행 →</button>
  </div>
</form>"""
    return page(s, center)


# ---------- 화면: reframe ----------
def render_reframe(s):
    r = s.get("reframe", {})
    verdict = r.get("userVerdict")
    vtag = ""
    if verdict == "approved":
        vtag = badge("승인됨", "bd green")
    elif verdict == "revise":
        vtag = badge("수정 요청됨", "bd gold")
    blocks = [
        ("최초 진술", r.get("initialStatement", ""), "당신이 처음 만들고 싶다고 말한 것", ""),
        ("관찰된 문제", r.get("observedProblem", ""), "인터뷰의 사건들이 실제로 가리키는 문제", "blue"),
        ("더 깊은 문제", r.get("deeperProblem", ""), "그 문제의 뿌리 — 반복해서 발견된 구조", "gold"),
        ("사업 기회", r.get("opportunityStatement", ""), "이 문제와 당신의 자산이 만나는 지점", "green"),
    ]
    cards = ""
    for title, body, hint, cls in blocks:
        border = {"blue": "var(--blue)", "gold": "var(--gold)", "green": "var(--sprout)"}.get(cls, "var(--line-strong)")
        cards += (f'<div class="card" style="border-left:4px solid {border}">'
                  f'<h3>{e(title)}</h3><p class="hint" style="margin:0 0 6px">{e(hint)}</p>'
                  f'<p style="font-size:15px;margin:0">{nl2br(body) or "—"}</p></div>')
    center = f"""
{phase_header(s, "reframe")}
<p class="sub">해결책을 잠시 내려놓고, 진짜 문제를 다시 정의했습니다. {vtag}</p>
<div class="thesis">이 재정의를 <b>당신이 승인해야</b> 다음 단계로 갑니다.
파운드리의 해석이 틀렸다면 수정을 요청하세요 — 문제 설정은 인간의 몫입니다.</div>
{cards}
<form method="post" action="/reframe">
  <label>수정 의견 (수정 요청 시)</label>
  <textarea class="short" name="comment" placeholder="예: '더 깊은 문제'는 동의하지만, 사업 기회는 검수 워크플로보다 교육에 가깝다고 생각합니다"></textarea>
  <div class="actions">
    <button class="green" name="verdict" value="approved" type="submit">이 재정의를 승인합니다 ✓</button>
    <button class="line" name="verdict" value="revise" type="submit">수정을 요청합니다</button>
  </div>
</form>"""
    return page(s, center)


# ---------- 화면: portfolio ----------
def render_portfolio(s):
    opps = s.get("opportunities", [])
    cards = ""
    for i, o in enumerate(opps):
        hz = o.get("horizon", "")
        g = (o.get("evidenceGrade") or "E").upper()
        cards += f"""<label class="opt" style="display:block;cursor:pointer">
<div class="card opp h-{e(hz)}"><div class="obar"></div>
  <div style="display:flex;align-items:flex-start;gap:10px">
    <input type="checkbox" name="opt" value="{i}" {"checked" if o.get("selected") else ""} style="margin-top:5px">
    <div style="flex:1;min-width:0">
      <h3>{e(o.get("name",""))}</h3>
      <div>{badge(HORIZON_LABEL.get(hz,hz),"bd acc")}{badge(o.get("form",""),"bd gold")}</div>
      <p style="font-size:14px;margin:8px 0 4px">{e(o.get("pitch",""))}</p>
      <div class="score-row">
        <span class="sc">잠재 가치 {score_dots(o.get("valueScore"))}</span>
        <span class="sc">창업자 적합성 {score_dots(o.get("fitScore"))}</span>
        <span class="sc"><span class="grade g{g}">{g}</span>{e(GRADE_HINT.get(g,""))}</span>
      </div>
      <p class="kv"><b>고객</b> {e(o.get("targetCustomer","")) or "—"} · <b>구매자</b> {e(o.get("buyer","")) or "—"}</p>
      <p class="kv"><b>구매 이유</b> {e(o.get("whyBuy","")) or "—"}</p>
      <p class="kv"><b>왜 당신인가</b> {e(o.get("whyYou","")) or "—"}</p>
      <p class="kv"><b>가장 큰 위험</b> {e(o.get("biggestRisk","")) or "—"} · <b>축적 자산</b> {e(o.get("assetBuilt","")) or "—"}</p>
    </div>
  </div>
</div></label>"""
    if not cards:
        cards = '<p class="hint">파운드리가 문제와 자산을 연결해 기회 포트폴리오를 주조하고 있습니다…</p>'
    center = f"""
{phase_header(s, "portfolio")}
<p class="sub">하나의 정답이 아니라 서로 다른 시간축의 기회들입니다.
지금 집중할 것을 1~2개 고르세요 — 고른 기회로 검증 실험을 설계합니다.</p>
<div class="thesis">점수는 판정이 아니라 대화의 시작입니다. 증거 등급 D·E 는
‘나쁜 기회’가 아니라 ‘검증이 먼저인 기회’라는 뜻입니다.</div>
<form method="post" action="/select-opps">
  {cards}
  <label>의견 (선택)</label>
  <textarea class="short" name="comment" placeholder="예: 1번이 끌리지만 시간이 부족합니다. 주 5시간으로 가능한 형태로 조정해 주세요"></textarea>
  <div class="actions"><button class="gold" type="submit">선택한 기회로 검증 설계 →</button></div>
</form>"""
    return page(s, center)


# ---------- 화면: validation ----------
def render_validation(s):
    exps = s.get("experiments", [])
    cards = ""
    for i, x in enumerate(exps):
        sel = badge("선택됨", "bd green") if x.get("selected") else ""
        cards += f"""<div class="card">
  <h3>{e(x.get("title",""))} {badge(str(x.get("days","?"))+"일","bd acc")} {sel}</h3>
  <p class="kv"><b>검증할 가장 위험한 가설</b> {e(x.get("riskiestAssumption","")) or "—"}</p>
  <form method="post" action="/select-exp">
    <input type="hidden" name="index" value="{i}">
    <div class="row">
      <div><label>실행할 행동</label><textarea class="short" name="action">{e(x.get("action",""))}</textarea></div>
      <div><label>대상 (누구에게)</label><textarea class="short" name="target">{e(x.get("target",""))}</textarea></div>
    </div>
    <div class="row">
      <div><label>측정 지표</label><textarea class="short" name="metric">{e(x.get("metric",""))}</textarea></div>
      <div><label>통과 기준</label><textarea class="short" name="passCriteria">{e(x.get("passCriteria",""))}</textarea></div>
    </div>
    <p class="kv"><b>실패 판정</b> {e(x.get("failCriteria","")) or "—"} · <b>중단 기준</b> {e(x.get("stopCriteria","")) or "—"} · <b>비용</b> {e(x.get("cost","")) or "0"}</p>
    <div class="actions"><button class="small gold" type="submit">이 실험 선택 →</button></div>
  </form>
</div>"""
    if not cards:
        cards = '<p class="hint">파운드리가 가장 위험한 가설을 겨냥한 실험을 설계하고 있습니다…</p>'
    center = f"""
{phase_header(s, "validation")}
<p class="sub">제품을 만들기 전에, 7~14일 안에 실행 가능한 가장 작은 실험으로
문제와 지불 의사를 확인합니다.</p>
<div class="thesis">실험에는 반드시 판정 가능한 지표와 실패·중단 기준이 있어야 합니다.
“반응이 좋으면”은 지표가 아닙니다.</div>
{cards}
<p class="foot">행동·대상·지표·기준은 직접 고친 뒤 선택하세요. 개발 없이 할 수 있는 것을 우선합니다.</p>"""
    return page(s, center)


# ---------- 화면: report ----------
def render_report(s):
    rp = s.get("reportPath", "")
    outputs = []
    outdir = os.path.join(SESSION_DIR, "outputs")
    if os.path.isdir(outdir):
        for fn in sorted(os.listdir(outdir)):
            if fn.startswith("."):
                continue
            outputs.append(fn)
    files = ""
    for fn in outputs:
        files += f'<li><a href="/outputs/{e(fn)}" target="_blank"><code>{e(fn)}</code></a></li>'
    if not files:
        files = '<li class="eempty">아직 생성된 산출물이 없습니다. 아래 버튼으로 생성하세요.</li>'
    gr = s.get("gateReport", "")
    grblock = f'<div class="card"><h3>하드 게이트 검사 결과</h3><pre style="font-family:var(--mono);font-size:12px;white-space:pre-wrap;margin:0">{e(gr)}</pre></div>' if gr else ""
    gen_btn = ("보고서 다시 생성" if rp else "최종 산출물 생성")
    center = f"""
{phase_header(s, "report")}
<p class="sub">인터뷰의 모든 발견이 추적 가능한 문서로 주조됩니다.
주요 주장에는 사실·추론·가설·제안·결정 표식과 근거 ID 가 붙습니다.</p>
{grblock}
<div class="card"><h3>산출물</h3><ul style="margin:6px 0;padding-left:20px;font-size:14px">{files}</ul>
<p class="hint">report.html 을 열고 브라우저 인쇄(⌘P)로 PDF 저장이 가능합니다 (print.css 내장).</p></div>
<form method="post" action="/report"><div class="actions">
  <button class="gold" type="submit">{e(gen_btn)} →</button>
</div></form>
<div class="thesis">기획서는 끝이 아니라 시작입니다. 가장 위험한 가설은 아직 검증되지 않았습니다 —
이번 주에 실험부터 시작하세요.</div>
<p class="foot">세션 기록은 이 폴더의 state.json 에 저장되어 있습니다. 스킬을 다시 불러 이어갈 수 있고,
폴더를 삭제하면 모든 데이터가 사라집니다 (전부 로컬).</p>"""
    return page(s, center)


RENDER = {"contract": render_contract, "graph": render_graph, "capability": render_capability,
          "reframe": render_reframe, "portfolio": render_portfolio,
          "validation": render_validation, "report": render_report}


def render(s):
    p = s.get("phase", "contract")
    if p in INTERVIEW_PHASES:
        return render_interview(s)
    return RENDER.get(p, render_contract)(s)


# ---------- HTTP handler ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _form(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        return parse_qs(raw, keep_blank_values=True)

    def _one(self, f, k, d=""):
        return f.get(k, [d])[0]

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/favicon.ico":
            return self._send(204, b"")
        if path == "/state":
            s = load_state()
            return self._send(200, json.dumps(
                {"version": s.get("version"), "phase": s.get("phase"),
                 "processing": bool(s.get("processing")), "notice": s.get("notice", ""),
                 "title": (s.get("session") or {}).get("title", ""), "sessionDir": SESSION_DIR}),
                "application/json")
        if path.startswith("/outputs/"):
            rel = unquote(path[len("/outputs/"):])
            fp = os.path.normpath(os.path.join(SESSION_DIR, "outputs", rel))
            if not fp.startswith(os.path.join(SESSION_DIR, "outputs")) or not os.path.isfile(fp):
                return self._send(404, "not found", "text/plain; charset=utf-8")
            ctype = mimetypes.guess_type(fp)[0] or "text/plain"
            if ctype.startswith("text/") or ctype in ("application/json",):
                ctype += "; charset=utf-8"
            with open(fp, "rb") as f:
                return self._send(200, f.read(), ctype)
        s = load_state()
        return self._send(200, render(s))

    def _redirect(self):
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        f = self._form()
        g = lambda k, d="": self._one(f, k, d)

        if path == "/start":
            fields = {k: g(k, "").strip() for k in
                      ("mode", "purpose", "goalType", "depthConsent", "offLimits",
                       "desiredDecision", "initialStatement")}
            def m(s):
                s["session"].update(fields)
                s["processing"] = True
                s["notice"] = "계약을 확인하고 첫 질문을 준비하고 있습니다…"
                s["pendingAction"] = {"type": "start_session", **fields}
            mutate(m)

        elif path == "/answer":
            def m(s):
                txt = g("text", "").strip()
                if txt:
                    s.setdefault("thread", []).append(
                        {"role": "user", "content": txt, "kind": "answer", "phase": s.get("phase")})
                s["currentQuestion"] = None
                s["processing"] = True
                s["notice"] = "답을 듣고 있습니다…"
                s["pendingAction"] = {"type": "answer", "text": txt}
            mutate(m)

        elif path == "/choose":
            idxs = [int(x) for x in f.get("opt", [])]
            def m(s):
                s["processing"] = True
                s["pendingAction"] = {"type": "answer_multi", "indices": idxs}
            mutate(m)

        elif path == "/interview":
            op = g("op", "skip")
            def m(s):
                s["processing"] = True
                s["pendingAction"] = {"type": "interview", "op": op}
            mutate(m)

        elif path == "/advance":
            def m(s):
                s["processing"] = True
                s["notice"] = "이 게이트의 산출물을 정리하고 있습니다…"
                s["pendingAction"] = {"type": "advance"}
            mutate(m)

        elif path == "/graph-feedback":
            node_id = g("nodeId", "")
            verdict = g("verdict", "confirmed")
            comment = g("comment", "").strip()
            def m(s):
                for n in (s.get("graph") or {}).get("nodes", []):
                    if n.get("id") == node_id:
                        n["status"] = verdict
                s["processing"] = True
                s["notice"] = "피드백을 그래프에 반영하고 있습니다…"
                s["pendingAction"] = {"type": "graph_feedback", "nodeId": node_id,
                                      "verdict": verdict, "comment": comment}
            mutate(m)

        elif path == "/graph-done":
            def m(s):
                s["processing"] = True
                s["pendingAction"] = {"type": "graph_done"}
            mutate(m)

        elif path == "/capability":
            op = g("op", "ok")
            comment = g("comment", "").strip()
            def m(s):
                s["processing"] = True
                s["pendingAction"] = {"type": ("capability_fix" if op == "fix" else "capability_ok"),
                                      "comment": comment}
            mutate(m)

        elif path == "/reframe":
            verdict = g("verdict", "approved")
            comment = g("comment", "").strip()
            def m(s):
                s["reframe"]["userVerdict"] = verdict
                s["processing"] = True
                s["notice"] = ("재정의를 승인했습니다. 다음 게이트를 준비합니다…"
                               if verdict == "approved" else "재정의를 다시 벼리고 있습니다…")
                s["pendingAction"] = {"type": "reframe_verdict", "verdict": verdict, "comment": comment}
            mutate(m)

        elif path == "/select-opps":
            idxs = [int(x) for x in f.get("opt", [])]
            comment = g("comment", "").strip()
            def m(s):
                for i, o in enumerate(s.get("opportunities", [])):
                    o["selected"] = i in idxs
                s["processing"] = True
                s["notice"] = "선택한 기회로 검증 실험을 설계하고 있습니다…"
                s["pendingAction"] = {"type": "select_opportunities", "indices": idxs, "comment": comment}
            mutate(m)

        elif path == "/select-exp":
            idx = int(g("index", "0") or 0)
            edits = {k: g(k, "") for k in ("action", "target", "metric", "passCriteria")}
            def m(s):
                exps = s.get("experiments", [])
                if 0 <= idx < len(exps):
                    exps[idx].update(edits)
                    for j, x in enumerate(exps):
                        x["selected"] = (j == idx)
                s["processing"] = True
                s["notice"] = "실험을 확정하고 산출물을 준비합니다…"
                s["pendingAction"] = {"type": "select_experiment", "index": idx, "edits": edits}
            mutate(m)

        elif path == "/nav":
            to = g("to", "contract")
            def m(s):
                s["processing"] = True
                s["pendingAction"] = {"type": "nav", "to": to}
            mutate(m)

        elif path == "/report":
            def m(s):
                s["processing"] = True
                s["notice"] = "산출물을 주조하고 있습니다… (게이트 검사 → 문서 생성)"
                s["pendingAction"] = {"type": "report"}
            mutate(m)

        self._redirect()


def pick_port(p):
    for cand in [p] + list(range(8931, 8970)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as t:
                t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                t.bind(("127.0.0.1", cand))
            return cand
        except OSError:
            continue
    return p


if __name__ == "__main__":
    os.makedirs(SESSION_DIR, exist_ok=True)
    load_state()
    port = pick_port(REQ_PORT)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"SF_SERVER_READY http://127.0.0.1:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
