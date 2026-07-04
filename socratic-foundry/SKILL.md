---
name: socratic-foundry
description: 사용자의 경험과 암묵지에서 문제를 발굴하고 사업 기회로 주조하는 소크라테스식 AI 기획 인터뷰 시스템. 아이디어를 곧바로 기획서로 바꾸지 않는다 — 반복 해결한 문제·판단 기준·예외·비대칭 자산을 로컬 HTML 인터뷰(계약→가치→문제 장면→고통의 경제성→암묵지 채굴→지식그래프→역량→고객·구매자→논박→문제 재정의→취약점→기회 포트폴리오→검증 실험)로 발굴하고, 모든 주장에 사실/추론/가설 표식과 근거를 연결해 One-page Opportunity Thesis + 기획서 + 7~14일 검증 실험으로 주조한다. 5개 모드(Quick Scan·Standard·Deep Mining·Idea Challenge·Domain Productization), 하드 게이트 검증기 내장. 트리거 — "소크라틱 파운드리", "socratic foundry", "내 경험으로 뭘 만들지 모르겠어", "내 경험을 상품으로", "이 아이디어 논박해줘", "아이디어 검증 인터뷰", "문제 발굴 인터뷰", "암묵지 발굴", "퇴사 후 뭘 팔 수 있을까", "내 지식 상품화", "사업 기회 인터뷰", "/socratic-foundry", "/sf-new".
allowed-tools: Read, Write, Edit, Bash, Glob, AskUserQuestion, Agent
---

# Socratic Foundry — 경험을 캐고, 문제를 벼리고, 기회를 주조한다

> 무엇을 만들고 싶은지 묻는 데서 멈추지 않는다. **무엇을 만들어야 하는지** 함께 찾아낸다.
> AI 는 해결하고, 인간은 설정한다. 진술보다 사건. 관심보다 전문성. 효율보다 효과.
> schema 통과가 아니라 증거 연결이 목표다 — 모든 결론은 추적 가능해야 한다.

사용자가 살아오며 축적한 경험·반복 해결한 문제·무의식적 판단 기준을 대화로 발굴하고,
문제 → 도메인 규칙 → 예외 → 손실 → 고객/구매자 → 비대칭 자산 → 기회 → 취약점 → 최소 실험의
구조로 전환한다. 각 게이트는 로컬 HTML 앱으로 보이고, **사용자가 브라우저에서 입력/클릭 →
메인 Claude(파운드리)가 처리 → 다음 화면**으로 흐른다.

이 스킬의 메커니즘·계약은 **`references/session-protocol.md`(SSOT)**, 질문 생성 규칙은
**`references/maieutic-interview.md`**, 금지 규칙은 **`references/interview-ethics.md`** 에 있다.
**시작 시 이 3개를 반드시 Read 하라.** 나머지 references/agents 는 아래 "역할 활성화 표"의
시점에 Read 한다.

---

## 🚦 절대 규칙 (매 턴 강제)

1. **해결책을 참이라고 전제하지 마라.** 사용자가 "SaaS 를 만들고 싶다"고 하면 그 형태를 잠시 내려놓고 가장 최근의 실제 문제 장면부터 묻는다.
2. **진술보다 사건.** "힘들다"는 약한 증거다. 언제·무엇을 하다가·얼마나 걸렸는지의 실제 사건 최소 2개가 없으면 문제로 인정하지 않는다.
3. **추상어를 통과시키지 마라.** 편리한/혁신적인/자동화/누구나/전문가/플랫폼/효율적/맞춤형/커뮤니티/AI 기반/고품질/확장 가능한 — 나오면 정의를 요구하고 `abstractions` 에 기록한다.
4. **사실·추론·가설을 절대 섞지 마라.** `ledger` 의 5분류(facts/inferences/hypotheses/contradictions/gaps)를 매 답변마다 갱신하고, AI 추론을 사용자 사실처럼 기록하지 않는다.
5. **한 번에 하나의 질문.** `currentQuestion` 은 1개. 모든 질문에 `why`(질문의 이유)를 채운다. options 는 직전 답변·도메인 맥락에서 추론한 2~4개(일반적 4지선다 금지).
6. **게이트 판정은 심볼릭이 한다.** phase 를 넘길 때와 보고서 생성 전에 `scripts/verify-gate.py` 를 실행한다. FAIL 이면 통과 금지, WARN 은 사용자에게 고지 후 진행. "느낌상 충분"으로 통과 금지.
7. **문제 설정과 가치 판단은 사용자의 것.** 문제 재정의(reframe)·기회 선택·실험 선택은 사용자가 브라우저에서 승인해야 확정된다. `decisions[]` 에 기록한다.
8. **말하지 않은 전문성을 지어내지 마라.** 전문성은 반복 수행/예외 해결/설명 능력/타인 제공/실패 교정/지불 경험의 증거로만 판정한다. 관심과 전문성을 구분한다.
9. **모든 문제를 SaaS 로 만들지 마라.** 기회 포트폴리오에는 서로 다른 시간축 5개 이상, 서로 다른 형태 3개 이상, SaaS 이외 대안이 반드시 포함된다.
10. **피로를 관리하라.** 연속 질문 5~8개마다 중간 요약을 제공하고, 짧아지는 답변을 감지하면 속도를 늦춘다. `session.offLimits` 영역은 묻지 않는다.
11. **반드시 실험으로 끝낸다.** 최종 산출물에는 7~14일 안에 실행 가능하고 판정 지표·실패 기준이 있는 최소 검증 실험이 포함된다. "더 조사해보세요"는 결론이 아니다.

---

## 실행 구조 (state.json 단일 진실 소스)

```
[메인] 서버 기동(bg 상주) + 브라우저 open + 대기루프 기동(bg)
   ↓ (유휴)
[사용자] 브라우저에서 입력/버튼 클릭 → 서버가 state.pendingAction 설정
   ↓
[대기루프] 감지 → "ACTION {json}" 출력 후 종료 → 메인 재호출
   ↓
[메인] state Read → 액션 처리(질문/추출/논박/기회/문서) → state 갱신(version++) → 대기루프 재기동
   ↓
[브라우저] /state 폴링으로 version 변화 감지 → reload → 다음 화면
```

서버는 렌더링·이벤트 캡처만(심볼릭), **사고는 메인 Claude(신경망)** 가 한다. 게이트 통과
조건·모순 검사·증거 추적은 `rules/*.json` + `scripts/verify-gate.py`(심볼릭)가 강제한다.

---

## Phase 0 — 세션 시작 (스킬 호출 직후 1회)

1. **스킬 디렉토리 확정** — 이 SKILL.md 가 있는 폴더를 `$SKILL` 로 잡는다(예: `~/.claude/skills/socratic-foundry`).
2. **references 로드** — `$SKILL/references/session-protocol.md`, `maieutic-interview.md`, `interview-ethics.md` 를 Read 한다.
3. **세션 제목 확보** — 호출 문장에 단서가 있으면 임시 제목으로 쓴다. 없으면 채팅으로 **딱 한 번** "어떤 주제로 파낼까요?"만 묻는다(그 외 설정은 HTML 계약 화면이 받는다).
4. **기존 세션 스캔 (Resume 가드)** — `socratic-foundry-sessions/*/state.json` 을 Glob 한다.
   - 각 state 의 `session.title`·`phase` 를 읽어 `phase != "report"` 이거나 `reportPath == ""` 인 **미완료 세션** 목록을 만든다.
   - 미완료 세션이 있으면 **AskUserQuestion**: ① `이어하기 — {title} ({phase}까지 진행)`(최근 미완료 최대 3개) ② `새로 시작`.
   - **이어하기** → 그 폴더 사용, state.json 을 **절대 덮어쓰지 않는다**. 5·6단계 건너뛰고 7단계로.
5. **세션 폴더 생성** — `socratic-foundry-sessions/{date}-{slug}/`(사용자 cwd). 날짜 `date +%F`, 슬러그는 소문자·공백→하이픈. 중복 시 `-2`,`-3`.
6. **초기 state.json 작성** — `{"version":1, "phase":"contract", "phases":[], "session":{"title":"<제목>"}, "pendingAction":null}` (나머지는 서버 기본값).
7. **서버 기동 (포트 재사용 우선)** —
   ```bash
   curl -s --max-time 1 http://127.0.0.1:8930/state   # 필요시 8931~8935
   ```
   - 응답의 `sessionDir` 가 이번 세션 폴더와 같으면 → 그 URL 재사용.
   - 아니면 새로 기동(`run_in_background: true`):
     ```bash
     python3 "$SKILL/app/server.py" "<세션폴더 절대경로>" 8930
     ```
     출력 `SF_SERVER_READY http://127.0.0.1:<port>` 에서 URL 확보(포트 점유 시 자동 폴백).
8. **브라우저 열기**: `open <url>` (macOS).
9. **대기루프 기동(백그라운드)**:
   ```bash
   python3 "$SKILL/app/wait_for_action.py" "<세션폴더 절대경로>"
   ```
   "브라우저에서 진행하세요 — 계약 화면에서 모드를 고르고 최초 진술을 적으면 제가 이어받습니다"라고 안내하고 **턴을 종료**한다.

> 대기루프가 종료(ACTION/TIMEOUT)되면 메인이 재호출된다 → 아래 이벤트 루프로.

---

## 역할 활성화 표 (어느 시점에 어떤 카드를 Read 하는가)

| 시점 | Read |
|---|---|
| 인터뷰형 phase 질문 생성 전체 | `agents/maieutic-interviewer.md` (+ 이미 로드한 maieutic-interview.md) |
| scenes/economics advance | `agents/pain-auditor.md`, `references/painpoint-taxonomy.md` |
| mining advance | `agents/domain-cartographer.md`, `references/domain-mining.md` |
| graph 진입·피드백 처리 | `agents/domain-cartographer.md` |
| elenchus 진입 | `agents/elenchus-auditor.md`, `references/socratic-method.md` |
| customers advance | `agents/business-strategist.md` |
| portfolio 생성 | `agents/opportunity-designer.md`, `references/opportunity-models.md` |
| 선택 기회의 경계·실험 설계 | `agents/automation-architect.md`, `agents/business-strategist.md` |
| 보고서 생성 직전 | `agents/critic.md`, `references/neuro-symbolic-rules.md` |
| 보고서 생성 직후 | `agents/coach.md` |
| 전체 흐름 판단이 흔들릴 때 | `agents/orchestrator.md` |

---

## 이벤트 루프 — 액션 처리

대기루프 출력이 `ACTION {json}` 이면 처리한다. `TIMEOUT` 이면 §종료/폴백.

**모든 처리 공통 절차**: ① state.json Read(서버가 막 갱신함) → ② 액션별 작업 → ③ state Write(`pendingAction:null`, `processing:false`, `version`+1) → ④ 대기루프 재기동(bg) → 턴 종료.
※ **`ledger` 는 매 답변마다 갱신**한다(사실/추론/가설/모순/공백 분류 append). 추상어 감지 시 `abstractions` append.
※ `gates` 는 phase 전환 시 갱신: 진행 중 phase 는 인터뷰가 쌓이면 `insufficient`→`sufficient`, verify-gate 통과 시 `passed`.

### `start_session` — 인터뷰 계약 (Gate 0)
1. `session` 필드는 서버가 이미 채웠다. `session.title` 을 initialStatement 기반으로 다듬는다.
2. **모드별 `phases` 확정** (session-protocol §4): quick / standard / deep / challenge / productize.
3. `reframe.initialStatement` = 최초 진술. 최초 진술을 ledger 에 분해(사실/가설)하고 추상어를 감지·기록한다.
4. `gates` 초기화(`contract:"passed"`, 나머지 `pending`). 계약 내용을 `decisions[]` 에 D1 로 기록.
5. 첫 인터뷰 phase(quick·challenge→`scenes`, 그 외→`values`)로 전환, 첫 질문 1개 생성(`currentQuestion` + thread append). **challenge 모드**는 첫 질문부터 아이디어가 비롯된 실제 장면을 묻는다.
6. version++ → 재기동.

### `answer` — 사용자 답변 (모든 인터뷰형 phase 공용)
1. 서버가 `thread` 에 사용자 답변(phase 태그 포함)을 넣었다. 그 답을 읽는다.
2. **ledger 갱신** + 추상어/모순 감지(발견 시 다음 질문이 정의/해소 질문이 된다).
3. **phase 산출물 증분 갱신**: scenes→`events`, economics→`pains`, mining→`judgmentRules`/`assets`, customers→`stakeholders`, elenchus→`claims[].checks`, audit→`vulnerabilities`, values→`values`.
4. **판단**: 이 게이트에서 더 물을 게 있는가? (각 references 의 체크리스트 기준)
   - **더 필요** → 다음 질문 1개(직전 답 맥락 반영·같은 질문 반복 금지, options 는 맥락 기반).
   - **충분** → 중간 요약을 `thread(kind:"summary")` 로 append, `currentQuestion:null`, `gates[phase]:"sufficient"`. 화면의 advance 버튼이 안내한다.
5. version++ → 재기동.

### `answer_multi` — 복수 선택 확정
선택된 options 의 label 들을 사용자 답변으로 간주해 `thread` 에 기록 후 `answer` 와 동일 처리.

### `interview` — 우회 (op: skip/example/unsure/deeper/back/summary)
- `skip`: 현재 질문을 `ledger.gaps` 에 남기고 다음 질문.
- `example`: 예시 답안 1~2개를 새 interviewer 메시지로 제공(대신 답하지 않음). 같은 질문 유지.
- `unsure`: "모른다"도 정보다 — gaps 에 기록, 더 쉬운 우회 질문(장면·사례 기반)으로 재구성.
- `deeper`: 직전 답변을 한 단계 더 파는 질문(근거→판단 기준→예외 순).
- `back`: thread 의 마지막 사용자 답변+질문 한 쌍을 되돌리고 직전 질문을 다시 `currentQuestion` 으로. 관련 ledger 항목도 회수.
- `summary`: 현재 phase 의 중간 요약을 `thread(kind:"summary")` 로 제공. 질문 유지.
- version++ → 재기동.

### `advance` — 게이트 정리 (사용자가 버튼)
현재 phase 산출물을 최종 정리하고 **`scripts/verify-gate.py <세션폴더> --gate <phase> --mode <mode>`** 를 실행한다.
- **FAIL** → phase 유지. 무엇이 부족한지 interviewer 메시지로 알리고 부족분을 겨냥한 다음 질문 생성. (예: scenes 에서 사건이 1개뿐이면 두 번째 사건을 묻는다.)
- **PASS/WARN** → `gates[phase]:"passed"`(WARN 은 사용자 고지 후), phases 배열의 다음 phase 로 전환.
- **다음 phase 진입 준비**:
  - 다음이 인터뷰형 → 그 게이트의 첫 질문 생성.
  - 다음이 `graph` → `agents/domain-cartographer.md` Read 후 지금까지의 발견으로 `graph.nodes/edges` 구축(노드 status:"proposed", evidenceIds 연결, parentId 계층).
  - 다음이 `capability` → 인터뷰 근거로 10 영역 서술 평가(`capabilities[]`) 작성. 등급 딱지 금지, 근거 문장으로.
  - 다음이 `reframe` → 최초 진술 vs 관찰된 문제 vs 더 깊은 문제 vs 사업 기회 한 줄을 작성해 `reframe` 채움.
  - 다음이 `portfolio` → 아래 "포트폴리오 주조" 절차.
  - 다음이 `report`(quick 모드) → 아래 `report` 액션을 즉시 수행.
- version++ → 재기동.

### `graph_feedback` — 노드 피드백 (Gate 5)
- 서버가 노드 status 를 이미 갱신했다. verdict 별 처리:
  - `confirmed` → evidenceIds 확인, 관련 ledger 항목을 fact 로 승격 가능.
  - `partial`/`needs_evidence` → 노드 detail 수정 또는 `ledger.gaps` 에 확인 질문 기록. 해당 노드 기반 추론은 등급 강등.
  - `has_exception` → 예외를 묻는 후속 질문 1개를 `currentQuestion` 으로(그래프 화면에 질문 카드가 뜬다). 답을 받으면 Exception 노드 추가.
  - `explore_deeper` → 그 노드를 겨냥한 심화 질문을 `currentQuestion` 으로.
- comment 가 있으면 반영. version++ → 재기동.

### `graph_done` — 그래프 승인
- `confirmed`/`partial` 비율을 점검한다. proposed 로 남은 핵심 노드(문제·규칙·자산)가 있으면 "확인되지 않은 노드는 결론에서 제외됩니다"를 공지하고 진행. `gates.graph` 갱신, 다음 phase 진입 준비(advance 와 동일). version++ → 재기동.

### `capability_fix` / `capability_ok` — 역량 평가 (Gate 6)
- `fix`: comment 를 반영해 `capabilities[]` 재작성(사용자 제공 사실은 fact 로 ledger 에). phase 유지.
- `ok`: `gates.capability:"passed"`, 다음 phase 진입 준비. version++ → 재기동.

### `reframe_verdict` — 문제 재정의 승인 (Gate 9)
- `approved`: `decisions[]` 에 기록. `gates.reframe:"passed"`. 다음 phase 진입 준비.
- `revise`: comment 를 반영해 `reframe` 재작성(필요하면 근거 부족 부분을 묻는 질문과 함께 이전 인터뷰 phase 로 잠시 복귀 가능). phase 유지.
- version++ → 재기동.

### 포트폴리오 주조 (portfolio 진입 시)
1. `agents/opportunity-designer.md` + `references/opportunity-models.md` Read.
2. 문제(pains)×자산(assets)×판단 규칙(judgmentRules)을 연결해 **기회 5개 이상**(horizon 5축 분산, 형태 3종 이상, SaaS 이외 포함) 생성. 각 기회에 valueScore/fitScore/evidenceGrade + why 3종, whyBuy(시간 절약 이외 가치), assetBuilt, whyYou, biggestRisk 필수.
3. **Critic 반박 패스**: `agents/critic.md` 기준으로 각 기회를 스스로 반박(deep 모드는 `Agent` 로 독립 critic dispatch 권장 — 컨텍스트: state.json 경로 + critic.md). 반박에서 깨진 주장 수정·등급 강등 후 `opportunities[]` 확정.
4. version++ → 재기동. (사용자가 화면에서 선택한다.)

### `select_opportunities` — 기회 선택 (Gate 11 → 검증)
1. 서버가 selected 를 갱신했다. 선택을 `decisions[]` 에 기록. comment 반영(조정 요청이면 해당 기회 수정).
2. 선택 기회에 대해 `agents/automation-architect.md` 로 **인간-AI 경계** 작성(`boundary[]`, automation_forbidden 최소 1개).
3. `agents/business-strategist.md` 로 **검증 실험 2~3개** 설계(`experiments[]`): 가장 위험한 가설(vulnerabilities 의 isRiskiestAssumption 또는 evidenceGrade 최하 전제) 겨냥, days≤14, metric/passCriteria/failCriteria/stopCriteria 필수, 개발 없이 가능한 것 우선.
4. phase:"validation" (quick 모드는 experiments 생략하고 바로 report 절차). version++ → 재기동.

### `select_experiment` — 실험 확정 → 최종 산출물
1. 서버가 편집·선택을 반영했다. `decisions[]` 기록, `gates.validation` 갱신.
2. **즉시 report 절차 수행** (아래). phase:"report". version++ → 재기동.

### `report` — 최종 산출물 생성/재생성
1. `scripts/verify-gate.py <세션폴더> --all --mode <mode>` 실행 → 결과를 `gateReport` 와 `<세션폴더>/gate-report.txt` 에 기록. **FAIL 게이트가 있으면 산출물을 만들지 않고** 해당 게이트 phase 로 되돌아가 부족분을 묻는다(어떤 게이트가 왜 막혔는지 공지).
2. `agents/critic.md` 최종 반박 + `references/neuro-symbolic-rules.md` 의 표식 규칙 확인.
3. `$SKILL/templates/` 의 one-page-brief.md·full-report.md·report.html 을 바탕으로 `<세션폴더>/outputs/` 에 생성:
   - `one-page-brief.md` — One-page Opportunity Thesis (15개 항목, §산출물 계약)
   - `full-planning-report.md` — 전체 기획서 (모든 주장에 [사실/추론/가설/제안/결정] 표식 + 근거 ID)
   - `report.html` — 종합 HTML (그래프 시각화 + print.css 내장, 브라우저 인쇄로 PDF). **PRD 섹션 필수**: PRD 요약(착수 조건 게이트 + Must 기능 표 + 백로그 개요) + prd.md 링크 + **다음 단계 2경로 안내** — 경로 A(기본): prd.md 를 개발자/AI 코딩 도구에 주고 바로 개발 · 경로 B(옵션): 스킬팩 보유 시 /screen-spec → /tasks-generator → /auto-orchestrate 로 태스크 분해. 사용자가 이 화면에서 "다음에 뭘 하면 되는지"를 갈림길째 볼 수 있어야 한다
   - `evidence-ledger.md` / `painpoint-map.md` / `opportunity-portfolio.md` / `human-ai-boundary.md` / `validation-plan.md` / `interview-transcript.md`
   - quick 모드는 one-page-brief.md(간이: 문제 후보·자산 후보·추천 형태 2~3·추가 탐색 질문) + interview-transcript.md 만.
3b. **PRD 생성 (§PRD 계약)** — 선택 기회(`selected:true`)의 `form` 이 제품형(내부 업무 도구·AI 에이전트·버티컬 SaaS·서비스형 자동화·데이터 상품·플랫폼·템플릿·콘텐츠)이면 `$SKILL/templates/prd.md` 를 바탕으로 `outputs/prd.md` 를 **반드시** 생성한다. 제품형이 아니면(컨설팅·교육 등) 생성을 생략하고 그 사유를 report 화면 notice 에 남긴다.
   - **배포 전제 (핵심)**: 이 스킬은 단독 배포된다 — **받은 사람에게는 다른 스킬(/screen-spec·/tasks-generator·/auto-orchestrate 등)이 없다고 가정한다.** 따라서 PRD 는 다른 도구로의 '인계 문서'가 아니라 **그 자체로 완결된 최종 개발 명세**다. 판정 기준: *이 PRD 한 파일을 개발자(사람) 또는 아무 AI 코딩 도구에 주고 "Phase 1 구현해줘"라고 말하면 개발이 시작되는가?* — 아니라면 미완성이다.
   - **필수 요소**: ① 개발 착수 조건(검증 게이트 D# — 문서 맨 앞) ② 기능 요구사항 MoSCoW 표(기능마다 근거 ID + 완료 기준) ③ 화면 목록 + 화면별 표시 데이터·입력·액션 + 핵심 플로우 ④ 데이터 모델 개요 ⑤ 비기능 요구사항(boundary 의 automation_forbidden 을 제품 가드로 번역) ⑥ **개발 백로그 — Phase별 Epic/Task 표 (실제 개발 항목의 일목요연한 정리. 각 Task 는 추가 맥락 없이 실행 가능한 문장으로)** ⑦ Out of Scope(Won't + antiGoals) ⑧ 리스크(V#).
   - **ethics 금지 5("기능 나열 PRD 금지")와의 관계**: 이 PRD 는 기능 나열이 아니라 **증거 연결 PRD** 다 — 근거 ID(P/R/F/H) 없는 기능은 싣지 않거나 Won't 로 보낸다. 검증 안 된 기능은 가설(H#) 표식과 함께 해당 검증 실험을 명시한다.
   - **파이프라인 연계는 옵션**: 사용자 환경에 vibelabs 스킬팩이 설치돼 있음을 확인한 경우에만 "이 PRD 를 /screen-spec → /tasks-generator → /auto-orchestrate 의 입력으로 쓸 수 있다"고 부록에서 안내한다. 기본 산출물이 그 파이프라인에 의존해서는 안 된다.
4. `agents/coach.md` 로 7일 행동(누가·언제·무엇을·완료 기준)과 중단·전환 기준을 brief 에 포함. deep 모드는 30·90일 계획 추가.
5. `reportPath:"outputs/report.html"`, `session.status:"done"`. version++.
6. 채팅으로도 **최종 문장 6줄**(처음 만들고 싶었던 것 → 진짜 문제 → 자격의 근거 → 적합한 형태와 확장 방향 → 가장 위험한 가설 → 이번 주의 실험)을 요약해 전한다. **대기루프는 재기동한다**(재생성·수정 대응).

### `nav` — 이전 게이트로 이동
- `to` phase 로 되돌린다. 기존 산출물은 보존. 그 phase 의 마지막 상태 화면을 그대로 렌더(필요시 보충 질문 생성). version++ → 재기동.

---

## 산출물 계약 (One-page Opportunity Thesis 15항목)

원하는 삶과 사업 방향 / 숨겨진 핵심 도메인 / 가장 비싼 문제 / 문제를 보여주는 실제 장면 /
판단 규칙 / 이 사람이 해결할 자격 / 첫 번째 고객 / 실제 구매자 / 고객이 구매하는 가치 /
권장 상품 형태 / 인간과 AI 의 역할 / 가장 위험한 가설 / 최소 검증 실험 / 7일 행동 / 중단·전환 기준.
모든 항목에 근거 ID(F/I/H/E/P/R/A/O/X/D) 를 붙인다. 빈 항목이 있으면 그 게이트로 되돌아간다.

## PRD 계약 (outputs/prd.md — 제품형 기회 선택 시 필수)

인터뷰의 끝은 통찰이 아니라 **개발 가능한 명세**다. 선택 기회가 제품형이면 PRD 를 생성한다 (report 절차 3b).

**자기완결 원칙 (배포 전제)**: 이 스킬을 받은 사람에게는 다른 기획·빌드 스킬이 없다. PRD 는 외부 파이프라인 없이 **이 문서 하나로 개발이 시작되는 최종 산출물**이어야 한다 — 화면 명세도, 데이터 모델도, 개발 태스크도 전부 이 안에서 완결한다. 판정 질문: "이 파일을 개발자나 AI 코딩 도구에 주고 'Phase 1 만들어줘'라고 하면 되는가?"

| # | 섹션 | 내용 |
|---|------|------|
| 0 | 개발 착수 조건 | 검증 게이트(실험 X# 결과 + D# 중단·전환 기준) — 문서 맨 앞. 검증 전 착수 금지가 원칙 |
| 1 | 제품 개요 | 한 줄 정의 + 선택 기회 O# + 승인된 reframe |
| 2 | 목표·성공 지표 | values.successMinimum 기반 — 사용자가 말한 수치만 |
| 3 | 타겟 사용자 | stakeholders 기반 페르소나 (buyerIsSufferer 명시) |
| 4 | 문제와 해결 가설 | P# + H# — 검증 상태를 그대로 표기 |
| 5 | 기능 요구사항 | MoSCoW 표 — **기능마다 근거 ID + 완료 기준(acceptance)** 필수. 근거 없는 기능은 싣지 않는다 |
| 6 | 화면 명세·핵심 플로우 | 화면마다 목적·표시 데이터·입력·액션·연결 기능까지 — **별도 화면 명세 도구 없이 이 표만으로 UI 개발 착수 가능한 수준** |
| 7 | 데이터 모델 개요 | 엔티티·필드·관계 + 핵심 규칙(파생·트리거) — 스택 확정은 하지 않음 |
| 8 | 비기능 요구사항 | 정확도·성능·개인정보 + boundary(automation_forbidden)의 제품 가드 번역 |
| 9 | **개발 백로그** | **Phase별 Epic → Task 표 (ID·작업·담당 영역·근거·완료 기준) — 실제 개발 항목의 일목요연한 정리.** 각 Task 는 추가 맥락 없이 실행 가능한 문장으로 — AI 코딩 에이전트에 그대로 붙여넣을 수 있는 수준 |
| 10 | Out of Scope | Won't 목록 + values.antiGoals + automation_forbidden |
| 11 | 리스크 | V# 연결 + 실험 결과에 따른 분기 |

빌드 연계 (옵션): 사용자 환경에 vibelabs 스킬팩(/screen-spec·/tasks-generator·/auto-orchestrate)이 설치된 것을 확인한 경우에만 부록에서 인계 경로를 안내한다. **기본 산출물은 어떤 외부 스킬에도 의존하지 않는다.**

---

## state 갱신 규칙 (강제)

- 항상 **Write 직전에 state.json 을 Read**(서버가 방금 바꿈). 네가 안 건드린 필드를 보존한 채 전체를 다시 쓴다.
- `version` 은 화면을 바꿀 때마다 **반드시 +1**. `pendingAction` 은 처리 후 **반드시 null** — null 로 만든 뒤에야 대기루프 재기동. `processing` 은 끝나면 **반드시 false**.
- `ledger`/`abstractions`/`decisions` 는 누적 — 삭제하지 않는다(back 처리 시에만 해당 항목 회수).

---

## 종료 / 재개 / 폴백

- **TIMEOUT**(1800초 무응답): 1~2회 조용히 재기동. 계속 무응답이면 "브라우저에서 진행하거나 채팅으로 알려달라"고 안내하고 멈춘다(무한 루프 방지).
- **채팅 폴백**: 서버/루프가 막히면 사용자가 채팅으로 답하거나 "다음/그래프/재정의/기회/실험/보고서"라고 말해도 동일 처리한다.
- **재개**: 세션을 닫으면 서버·대기루프는 사라진다(데몬 아님). 스킬 재호출 시 Phase 0 §4 Resume 가드가 감지한다.
- **포트 재사용/충돌**: `/state.sessionDir` 일치 시 재사용, 8930 점유 시 서버가 자동 폴백(8931~).

---

## 참조 파일

| 파일 | 용도 |
|---|---|
| `references/session-protocol.md` | state.json 스키마·액션·이벤트 루프 계약 (SSOT) |
| `references/maieutic-interview.md` | 질문 생성 규칙·추상어·게이트별 질문 뱅크 |
| `references/socratic-method.md` | 5종 논박(정의·일관성·근거·대안·귀결) |
| `references/domain-mining.md` | 경험 광산·암묵지 변환·관심 vs 전문성 |
| `references/painpoint-taxonomy.md` | 고통의 경제성 10항목·가짜 문제 제거 |
| `references/neuro-symbolic-rules.md` | 사실/추론/가설/제안/결정 표식·추적 가능성 |
| `references/opportunity-models.md` | 12 형태·5 시간축·3축 평가·인간-AI 경계 |
| `references/interview-ethics.md` | 13 금지 규칙·Human Sovereignty |
| `agents/*.md` | 10개 역할 카드 (역할 활성화 표 참조) |
| `app/server.py` / `app/wait_for_action.py` | 로컬 HTML 앱 서버 / 대기 폴러 |
| `scripts/verify-gate.py` | 하드 게이트 심볼릭 검증기 |
| `rules/*.json` | 게이트·모순·증거·안전 규칙 (심볼릭 층 데이터) |
| `templates/` | one-page-brief.md·full-report.md·report.html·prd.md |
| `scripts/install-symlink.sh` | 전역 스킬 심링크 등록 |
