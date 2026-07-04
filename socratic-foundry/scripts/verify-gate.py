#!/usr/bin/env python3
"""
Socratic Foundry — 하드 게이트 심볼릭 검증기

state.json 을 rules/gate-rules.json 의 임계값으로 기계 검사한다. 메인 Claude(신경망)는
게이트 통과를 "느낌"으로 판정할 수 없다 — advance / report 전에 반드시 이 스크립트를 실행하고
FAIL 이 있으면 통과 금지, WARN 은 사용자 고지 후 진행한다 (뉴로심볼릭 분리).

사용법:
  python3 verify-gate.py <session_dir> --gate <phase> [--mode <mode>]
  python3 verify-gate.py <session_dir> --all [--mode <mode>]

출력: 줄 단위 "[PASS|WARN|FAIL] <gate> — <detail>"  + 마지막 줄 요약
종료코드: FAIL 1개 이상이면 1, 아니면 0
"""

import sys, os, json, argparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(SKILL_DIR, "rules", "gate-rules.json")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def nonempty(x):
    return bool(str(x or "").strip())


class Reporter:
    def __init__(self, warn_only_gates):
        self.lines = []
        self.fails = 0
        self.warns = 0
        self.warn_only = set(warn_only_gates)

    def ok(self, gate, msg):
        self.lines.append(f"[PASS] {gate} — {msg}")

    def warn(self, gate, msg):
        self.warns += 1
        self.lines.append(f"[WARN] {gate} — {msg}")

    def fail(self, gate, msg):
        if gate in self.warn_only:
            self.warns += 1
            self.lines.append(f"[WARN] {gate} — {msg} (모드 정책상 WARN 강등)")
        else:
            self.fails += 1
            self.lines.append(f"[FAIL] {gate} — {msg}")


# ---------- 게이트별 검사 ----------
def check_problem_events(s, t, r):
    g = "problem"
    events = s.get("events", [])
    if len(events) < t["min_events"]:
        r.fail(g, f"실제 사건 {len(events)}개 — 최소 {t['min_events']}개 필요 (진술보다 사건)")
    else:
        r.ok(g, f"실제 사건 {len(events)}개 확보")
    for ev in events:
        missing = [f for f in t["event_required_fields"] if not nonempty(ev.get(f))]
        if missing:
            r.fail(g, f"사건 {ev.get('id','?')} 필드 누락: {', '.join(missing)}")


def check_problem(s, t, r):
    g = "problem"
    check_problem_events(s, t, r)
    pains = s.get("pains", [])
    if len(pains) < t["min_pains"]:
        r.fail(g, f"고통 지점 {len(pains)}개 — 최소 {t['min_pains']}개 필요")
        return
    events = {ev.get("id"): ev for ev in s.get("events", [])}
    for p in pains:
        pid = p.get("id", "?")
        if t["pain_requires_frequency"]:
            try:
                if float(p.get("frequencyPerMonth") or 0) <= 0:
                    r.fail(g, f"{pid} 발생 빈도 미확인 (frequencyPerMonth)")
            except (TypeError, ValueError):
                r.fail(g, f"{pid} 발생 빈도가 수치가 아님")
        if not any(nonempty(p.get(f)) for f in t["pain_loss_fields"]):
            r.fail(g, f"{pid} 손실·위험 항목이 전부 비어 있음 (비용/오류/지연/이탈/매출/품질/법적/감정 중 1개 이상)")
        if t["pain_requires_workaround_in_events"]:
            linked = [events[i] for i in p.get("eventIds", []) if i in events] or list(events.values())
            if not any(nonempty(ev.get("workaround")) for ev in linked):
                r.fail(g, f"{pid} 현재 우회 방법(workaround) 미확인 — 버티는 방식을 물어야 함")


def check_domain(s, t, r):
    g = "domain"
    rules = s.get("judgmentRules", [])
    if len(rules) < t["min_judgment_rules"]:
        r.fail(g, f"판단 규칙 {len(rules)}개 — 최소 {t['min_judgment_rules']}개 필요")
    else:
        r.ok(g, f"판단 규칙 {len(rules)}개 확보")
    total_exc = 0
    for ru in rules:
        rid = ru.get("id", "?")
        if t["rule_requires_example"] and not nonempty(ru.get("example")):
            r.fail(g, f"{rid} 실제 사례(example) 없음 — 사례 없는 규칙은 인정 불가")
        if t["rule_requires_confidence"] and ru.get("confidence") not in ("experience", "talent", "unverified"):
            r.fail(g, f"{rid} confidence(경험/재능/미검증) 미구분 — 관심과 전문성을 구분해야 함")
        total_exc += len(ru.get("exceptions", []) or [])
    if total_exc < t["min_total_exceptions"]:
        r.fail(g, f"예외 {total_exc}개 — 최소 {t['min_total_exceptions']}개 필요 (예외 없는 규칙은 의심)")
    if len(s.get("assets", [])) < t["min_assets"]:
        r.fail(g, f"비대칭 자산 {len(s.get('assets', []))}개 — 최소 {t['min_assets']}개 필요")


def check_customer(s, t, r):
    g = "customer"
    st = s.get("stakeholders", {})
    missing = [f for f in t["required_fields"] if not nonempty(st.get(f))]
    if missing:
        r.fail(g, f"이해관계자 필드 누락: {', '.join(missing)}")
    else:
        r.ok(g, "사용자·구매자·첫 고객·접근 경로 정의됨")
    if t["buyer_is_sufferer_must_be_answered"] and not isinstance(st.get("buyerIsSufferer"), bool):
        r.fail(g, "'아픈 사람 = 내는 사람?' 미확인 (buyerIsSufferer)")


def check_evidence(s, t, r):
    g = "evidence"
    facts = (s.get("ledger") or {}).get("facts", [])
    if len(facts) < t["min_facts"]:
        r.fail(g, f"확인된 사실 {len(facts)}개 — 최소 {t['min_facts']}개 필요")
    else:
        r.ok(g, f"확인된 사실 {len(facts)}개")
    for o in s.get("opportunities", []):
        oid = o.get("id", "?")
        if t["opportunity_requires_grade"] and (o.get("evidenceGrade") or "").upper() not in "ABCDE":
            r.fail(g, f"{oid} 증거 등급 없음")
        if t["opportunity_requires_grade_why"] and not nonempty(o.get("gradeWhy")):
            r.fail(g, f"{oid} 등급 근거(gradeWhy) 없음 — 근거 없는 등급 금지")
    if t["unresolved_abstractions_block"]:
        unres = [a.get("term") for a in s.get("abstractions", []) if not a.get("resolved")]
        if unres:
            r.fail(g, f"정의되지 않은 추상어 잔존: {', '.join(map(str, unres))}")
    if t["open_contradictions_warn"]:
        opens = [c.get("id") for c in (s.get("ledger") or {}).get("contradictions", [])
                 if c.get("status") == "open"]
        if opens:
            r.warn(g, f"미해소 모순 {len(opens)}건({', '.join(map(str, opens))}) — 보고서에 '미해소 긴장'으로 명시할 것")


def check_opportunity(s, t, r, mode=""):
    g = "opportunity"
    opps = s.get("opportunities", [])
    min_n = t["min_opportunities_quick"] if mode == "quick" else t["min_opportunities"]
    if len(opps) < min_n:
        r.fail(g, f"기회 {len(opps)}개 — 최소 {min_n}개 필요 (서로 다른 시간축)")
    else:
        r.ok(g, f"기회 {len(opps)}개 생성")
    forms = {o.get("form") for o in opps if nonempty(o.get("form"))}
    if mode != "quick" and len(forms) < t["min_distinct_forms"]:
        r.fail(g, f"해결 형태 {len(forms)}종 — 최소 {t['min_distinct_forms']}종 비교 필요")
    if t["require_non_saas_alternative"] and opps and all("SaaS" in (o.get("form") or "") for o in opps):
        r.fail(g, "모든 기회가 SaaS — SaaS 이외 대안 검토 필수 (금지 규칙 S3)")
    horizons = {o.get("horizon") for o in opps if nonempty(o.get("horizon"))}
    if mode != "quick" and len(horizons) < t["min_distinct_horizons"]:
        r.fail(g, f"시간축 {len(horizons)}종 — 최소 {t['min_distinct_horizons']}종 필요 (즉시/상품/자동화/확장/옵션)")
    for o in opps:
        if o.get("selected") and t["selected_requires_fit_why"] and not nonempty(o.get("fitWhy")):
            r.fail(g, f"{o.get('id','?')} 선택됐지만 적합성 근거(fitWhy) 없음")


def check_value(s, t, r):
    g = "value"
    sel = [o for o in s.get("opportunities", []) if o.get("selected")]
    if not sel:
        r.warn(g, "선택된 기회 없음 — 선택 후 재검사")
        return
    for o in sel:
        oid = o.get("id", "?")
        if t["selected_requires_why_buy"] and not nonempty(o.get("whyBuy")):
            r.fail(g, f"{oid} 고객의 구매 이유(whyBuy) 없음 — 시간 절약 외 가치 확인 필요")
        if t["selected_requires_asset_built"] and not nonempty(o.get("assetBuilt")):
            r.fail(g, f"{oid} 축적 자산(assetBuilt) 없음 — 데이터·사례·신뢰 축적 여부 검토 필요")
    if not r.fails:
        r.ok(g, "선택 기회의 구매 이유·축적 자산 확인됨")


def check_sovereignty(s, t, r):
    g = "sovereignty"
    phases = s.get("phases", [])
    if t["reframe_requires_user_approval"] and "reframe" in phases:
        if (s.get("reframe") or {}).get("userVerdict") != "approved":
            r.fail(g, "문제 재정의가 사용자 승인되지 않음 (reframe.userVerdict)")
        else:
            r.ok(g, "문제 재정의 사용자 승인 완료")
    if len(s.get("decisions", [])) < t["min_decisions"]:
        r.fail(g, f"사용자 결정 기록 {len(s.get('decisions', []))}건 — 최소 {t['min_decisions']}건 (계약·재정의·선택)")
    if t["boundary_requires_forbidden_zone"] and "validation" in phases:
        if not any(b.get("mode") == "automation_forbidden" for b in s.get("boundary", [])):
            r.fail(g, "자동화 금지 영역(automation_forbidden) 미명시 — 최소 1개 필요")
    if t["session_requires_desired_decision"] and not nonempty((s.get("session") or {}).get("desiredDecision")):
        r.fail(g, "인터뷰 후 내릴 결정(desiredDecision) 미정의 (Gate 0 계약)")


def check_validation(s, t, r):
    g = "validation"
    sel = [x for x in s.get("experiments", []) if x.get("selected")]
    if len(sel) < t["min_selected_experiments"]:
        r.fail(g, f"선택된 실험 {len(sel)}개 — 최소 {t['min_selected_experiments']}개 필요")
        return
    for x in sel:
        xid = x.get("id", "?")
        try:
            if float(x.get("days") or 999) > t["max_days"]:
                r.fail(g, f"{xid} 기간 {x.get('days')}일 — {t['max_days']}일 이내여야 함 (제품 개발 전 검증)")
        except (TypeError, ValueError):
            r.fail(g, f"{xid} 기간(days)이 수치가 아님")
        missing = [f for f in t["experiment_required_fields"] if not nonempty(x.get(f))]
        if missing:
            r.fail(g, f"{xid} 필드 누락: {', '.join(missing)} — '반응이 좋으면'은 지표가 아님")
    if not r.fails:
        r.ok(g, f"판정 가능한 실험 {len(sel)}개 확정")


CHECKS = {
    "problem_events": lambda s, th, r, m: check_problem_events(s, th["problem"], r),
    "problem":        lambda s, th, r, m: check_problem(s, th["problem"], r),
    "domain":         lambda s, th, r, m: check_domain(s, th["domain"], r),
    "customer":       lambda s, th, r, m: check_customer(s, th["customer"], r),
    "evidence":       lambda s, th, r, m: check_evidence(s, th["evidence"], r),
    "opportunity":    lambda s, th, r, m: check_opportunity(s, th["opportunity"], r, m),
    "value":          lambda s, th, r, m: check_value(s, th["value"], r),
    "sovereignty":    lambda s, th, r, m: check_sovereignty(s, th["sovereignty"], r),
    "validation":     lambda s, th, r, m: check_validation(s, th["validation"], r),
}

ALL_GATES = ["problem", "domain", "customer", "evidence", "opportunity", "value", "sovereignty", "validation"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session_dir")
    ap.add_argument("--gate", help="advance 대상 phase 이름 (phase_gate_map 으로 매핑)")
    ap.add_argument("--all", action="store_true", help="모든 하드 게이트 검사 (report 전)")
    ap.add_argument("--mode", default="", help="모드 (미지정 시 state.session.mode)")
    args = ap.parse_args()

    state_path = os.path.join(os.path.abspath(args.session_dir), "state.json")
    if not os.path.isfile(state_path):
        print(f"[FAIL] system — state.json 없음: {state_path}")
        sys.exit(1)
    s = load(state_path)
    rules = load(RULES_PATH)
    th = rules["thresholds"]
    mode = args.mode or (s.get("session") or {}).get("mode") or "standard"
    mode_cfg = rules.get("modes", {}).get(mode, {})
    r = Reporter(mode_cfg.get("warn_only_gates", []))

    if args.all:
        gates = ALL_GATES
    elif args.gate:
        gates = rules.get("phase_gate_map", {}).get(args.gate, [])
        if not gates:
            print(f"[PASS] {args.gate} — 이 phase 는 기계 검사 대상 게이트가 없음 (신경망 판단 + 사용자 승인)")
            sys.exit(0)
    else:
        print("사용법: verify-gate.py <session_dir> (--gate <phase> | --all) [--mode <mode>]")
        sys.exit(2)

    for gname in gates:
        CHECKS[gname](s, th, r, mode)

    for line in r.lines:
        print(line)
    verdict = "FAIL" if r.fails else ("WARN" if r.warns else "PASS")
    print(f"—— 요약: {verdict} (fail {r.fails} / warn {r.warns}) · mode={mode} · gates={','.join(gates)}")
    sys.exit(1 if r.fails else 0)


if __name__ == "__main__":
    main()
