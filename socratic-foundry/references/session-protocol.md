# 세션 프로토콜 (SSOT) — state.json 스키마 · 액션 · 이벤트 루프 계약

> 이 문서는 `app/server.py`(렌더·이벤트 캡처)와 메인 Claude(Socratic Foundry 오케스트레이터)의 **유일한 계약**이다.
> 스키마를 바꾸면 server.py, SKILL.md 이벤트 루프, `scripts/verify-gate.py`, `rules/gate-rules.json` 을 함께 바꾼다.

---

## 1. 역할 분리 (뉴로심볼릭 §13)

| 주체 | 층 | 책임 |
|------|----|------|
| **server.py** | 심볼릭 | state.json 을 읽어 현재 `phase` 화면을 HTML 렌더. 사용자 입력(폼·버튼)을 `pendingAction` 으로 기록(version 불변). `processing` 배너 표시. |
| **wait_for_action.py** | 심볼릭 | `pendingAction` 이 채워질 때까지 폴링 → `ACTION {json}` 출력 후 종료. |
| **scripts/verify-gate.py** | 심볼릭 | `rules/gate-rules.json` 기준으로 state 의 하드 게이트 충족 여부를 기계 검사. |
| **메인 Claude** | 신경망 | `pendingAction` 을 받아 **사고 작업**(질문 생성·암묵지 분해·논박·기회 설계·문서 작성)을 수행하고 state 갱신(`version`++, `pendingAction:null`, `processing:false`). |

**철칙**: server 는 절대 사고하지 않는다(LLM 작업 0). 메인은 절대 HTML 을 직접 그리지 않는다(state 만 갱신). 사용자는 오직 브라우저에서만 입력한다. 게이트 통과 판정은 verify-gate.py 결과가 우선한다(메인의 "느낌"으로 통과 금지).

---

## 2. state.json 스키마

```jsonc
{
  "version": 1,                  // 브라우저 reload 트리거. 메인이 화면을 바꿀 때마다 +1.
  "phase": "contract",           // phases 배열의 원소 중 하나 + "report"
  "phases": [],                  // 모드별 레일. 모드 확정 시 메인이 채움 (§4 모드표)
  "processing": false,           // true 면 "생각 중…" 배너 + 버튼 비활성
  "notice": "",                  // 배너 문구 (선택)
  "pendingAction": null,         // 서버가 채우고, 메인이 처리 후 null 로 되돌림

  "session": {
    "title": "",                 // 세션 제목 (인터뷰 진행하며 정교화 가능)
    "mode": "",                  // quick | standard | deep | challenge | productize
    "purpose": "",               // Gate 0: 오늘 가장 알고 싶은 것
    "goalType": "",              // idea_validation | problem_discovery | productization
    "depthConsent": "",          // 어느 깊이까지 질문해도 되는가
    "offLimits": "",             // 공개하기 불편한 영역 (질문 금지 구역)
    "desiredDecision": "",       // 인터뷰가 끝나면 내릴 수 있어야 할 결정
    "initialStatement": "",      // 사용자의 최초 진술 원문 (아이디어/욕구)
    "status": "interviewing"     // interviewing | deciding | done
  },

  // ── 중앙: 인터뷰 스레드 (모든 인터뷰형 phase 공용) ──
  "thread": [
    // { "role": "interviewer"|"user", "content": "…",
    //   "kind": "question"|"answer"|"summary"|"probe", "phase": "scenes" }
  ],
  "currentQuestion": {           // 지금 던진 질문 1개. 없으면 null.
    "text": "",                  // 질문 본문 (반드시 한 번에 하나)
    "why": "",                   // 질문의 이유 (§16.2 '질문의 이유' — 항상 채운다)
    "gate": "",                  // 이 질문이 속한 게이트 (레일 하이라이트용)
    "options": [],               // 예상 답변 카드 [{ "label": "…", "hint": "…" }] (맥락 기반 2~4개)
    "allowMulti": false,         // options 다중 선택 허용
    "inputType": "text",         // text | scale (scale 이면 options 를 1~5 단계로 렌더)
    "placeholder": "",
    "allowSkip": true,
    "allowExample": true,
    "allowUnsure": true          // "잘 모르겠습니다" 버튼
  },

  // ── 우측: Evidence Panel (항상 누적, 절대 섞지 않음 §4.7) ──
  "ledger": {
    "facts": [],                 // 사실: 사용자가 제공했거나 자료로 확인됨   [{ "id":"F1", "content":"…", "source":"scenes#3" }]
    "inferences": [],            // 추론: 여러 사실을 연결해 도출            [{ "id":"I1", "content":"…", "basis":["F1","F3"] }]
    "hypotheses": [],            // 가설: 검증 필요                          [{ "id":"H1", "content":"…", "testedBy":"" }]
    "contradictions": [],        // 모순: [{ "id":"C1", "a":"…", "b":"…", "status":"open"|"resolved", "resolution":"…" }]
    "gaps": []                   // 지식 공백 / 미확인 질문 (문자열 배열)
  },
  "abstractions": [],            // 감지한 추상어 [{ "term":"자동화", "context":"…", "resolved":false, "definition":"" }]
  "decisions": [],               // 사용자 결정 [{ "id":"D1", "decision":"…", "phase":"reframe", "basis":"…" }]

  // ── Gate 산출물 ──
  "values": {                    // Gate 1
    "workStyle": "",             // 어떤 방식으로 일하고 싶은가
    "priorities": [],            // 돈/자율성/안정성/영향력/성장 우선순위 (중요한 순)
    "antiGoals": [],             // 원하지 않는 사업 방식 (금지 조건)
    "customerDepth": "",         // many_shallow | few_deep | undecided
    "teamPreference": "",        // solo | team | undecided
    "successMinimum": ""         // 성공했다고 판단할 최소 조건
  },

  "events": [                    // Gate 2: 실제 사건 (최소 2개)
    // { "id":"E1", "title":"…", "when":"…", "doing":"…", "actors":"…", "tools":"…",
    //   "stuckAt":"…", "timeTaken":"…", "workaround":"…", "gaveUp":"…", "quote":"…" }
  ],

  "pains": [                     // Gate 3: 고통의 경제성
    // { "id":"P1", "eventIds":["E1"], "description":"…",
    //   "frequencyPerMonth":0, "hoursPerOccurrence":0,
    //   "directCost":"", "errorCost":"", "delayCost":"", "churnRisk":"", "revenueLoss":"",
    //   "qualityRisk":"", "legalRisk":"", "emotionalLoad":"",
    //   "alreadyPaid":"", "unlockedIfSolved":"", "severityNote":"" }
  ],

  "judgmentRules": [             // Gate 4: 암묵지 → 판단 규칙 (최소 3개, 각 사례 필수)
    // { "id":"R1", "rule":"…", "signals":["…"], "example":"…", "exceptions":["…"],
    //   "noviceMistake":"…", "evidence":"…", "confidence":"experience|talent|unverified" }
  ],
  "assets": [                    // Gate 4/6: 비대칭 자산
    // { "id":"A1", "kind":"experience|data|materials|relationship|trust|skill",
    //   "description":"…", "evidence":"…", "replicability":"hard|medium|easy" }
  ],

  "graph": {                     // Gate 5: 도메인 지식그래프
    "nodes": [
      // { "id":"N1", "type":"Experience|PainPoint|JudgmentSignal|DomainRule|Exception|DomainAsset|Opportunity|Customer|Buyer|…(§14)",
      //   "label":"…", "detail":"…", "parentId":null,
      //   "status":"proposed|confirmed|partial|needs_evidence|has_exception|explore_deeper",
      //   "evidenceIds":["F1"] }
    ],
    "edges": []                  // [{ "from":"N1", "rel":"REVEALS|SUPPORTS|HAS_EXCEPTION|ENABLES|…(§14)", "to":"N2" }]
  },

  "capabilities": [              // Gate 6: 10 영역 서술 평가 (초급/중급/고급 금지)
    // { "area":"도메인 전문성|문제 해결력|기술 구현력|판매 경험|고객 접근성|콘텐츠 제작력|운영 능력|가용 시간|초기 자본|협업 자원",
    //   "assessment":"서술 문장", "evidence":"…", "gapNote":"…" }
  ],

  "stakeholders": {              // Gate 7
    "problemHaver": "", "user": "", "beneficiary": "", "buyer": "",
    "approver": "", "operator": "", "dataProvider": "", "blocker": "",
    "buyerIsSufferer": null,     // true | false | null(미확인)
    "statusQuoWinner": "",       // 기존 방식 유지로 이익 보는 사람
    "accessPath": "",            // 고객 접근 경로
    "firstCustomer": ""          // 첫 번째 고객 (구체적으로)
  },

  "claims": [                    // Gate 8: 소크라테스 논박 대상 핵심 주장
    // { "id":"CL1", "claim":"…", "status":"open|survived|revised|withdrawn",
    //   "checks":[ { "kind":"definition|consistency|evidence|alternative|consequence",
    //                "question":"…", "answer":"…", "verdict":"pass|fail|revised" } ] }
  ],

  "reframe": {                   // Gate 9: 문제 재정의 (사용자 승인 필수)
    "initialStatement": "",      // 최초 진술
    "observedProblem": "",       // 관찰된 문제
    "deeperProblem": "",         // 더 깊은 문제
    "opportunityStatement": "",  // 사업 기회 한 줄
    "userVerdict": null          // "approved" | "revise" | null
  },

  "vulnerabilities": [           // Gate 10: 취약점 감사
    // { "id":"V1", "category":"고객 접근 부족|지불 의사 불확실|…(§10 범주 13종)",
    //   "description":"…", "severity":"high|mid|low", "evidence":"…",
    //   "mitigation":"…", "isRiskiestAssumption":false }
  ],

  "opportunities": [             // Gate 11: 기회 포트폴리오 (최소 5개, 서로 다른 시간축)
    // { "id":"O1", "horizon":"now|product|automation|scale|option",
    //   "form":"컨설팅|진단 서비스|교육 상품|템플릿·콘텐츠|서비스형 자동화|내부 업무 도구|AI 에이전트|버티컬 SaaS|데이터 상품|커뮤니티|플랫폼|전략적 운영 모델",
    //   "name":"…", "pitch":"…", "targetCustomer":"…", "buyer":"…",
    //   "valueScore":3, "valueWhy":"…",          // 잠재 가치 1~5
    //   "fitScore":3, "fitWhy":"…",              // 창업자 적합성 1~5
    //   "evidenceGrade":"A|B|C|D|E", "gradeWhy":"…",
    //   "whyBuy":"…",                            // 고객의 구매 이유 (시간 절약 이외 가치 포함)
    //   "assetBuilt":"…",                        // 이 기회로 축적되는 자산 (데이터/사례/신뢰)
    //   "requiredAssets":["A1"], "biggestRisk":"…", "whyYou":"…", "selected":false }
  ],

  "boundary": [                  // §11 인간-AI 업무 경계
    // { "task":"…", "mode":"ai_only|ai_draft_human_review|human_decide_ai_execute|co_work|human_only|automation_forbidden", "reason":"…" }
  ],

  "experiments": [               // 검증 실험 (7~14일 안 실행 가능)
    // { "id":"X1", "title":"…", "riskiestAssumption":"…", "action":"…", "days":7,
    //   "target":"…", "metric":"…", "passCriteria":"…", "failCriteria":"…",
    //   "stopCriteria":"…", "cost":"…", "selected":false }
  ],

  "gates": {                     // 레일 상태 표시용. 값: pending|insufficient|sufficient|passed
    // phases 배열의 각 원소를 키로 사용. 예: { "contract":"passed", "scenes":"sufficient", … }
  },
  "gateReport": "",              // verify-gate.py 마지막 실행 결과 요약 (report 화면 표시용)
  "reportPath": ""               // 산출물 생성 후 outputs 상대경로
}
```

> **누락 필드 허용**: 메인이 초기 state 를 쓸 때 핵심(`version/phase/phases/session`)만 써도 된다. server 의 `default_state()` 가 나머지를 기본값으로 채운다. 단 **이미 존재하는 필드는 Write 시 보존**해야 한다(§6).
> **ID 규칙**: F/I/H/C(원장), E(사건), P(고통), R(규칙), A(자산), N(노드), CL(주장), V(취약점), O(기회), X(실험), D(결정) 접두사 + 순번. 모든 교차 참조는 이 ID 로 한다.

---

## 3. phase 카탈로그와 화면 유형

server.py 는 phase 를 **화면 유형(view)** 으로 매핑해 렌더한다.

| phase | 게이트 | 화면 유형 | 중앙 화면 | 주요 pendingAction |
|-------|--------|----------|----------|--------------------|
| `contract` | Gate 0 | contract | 모드 5종 카드 + 목적/깊이/금지영역/원하는 결정 + 최초 진술 | `{type:"start_session", fields…}` |
| `values` | Gate 1 | interview | 스레드 + 질문 카드 | `{type:"answer"…}` / `{type:"advance"}` |
| `scenes` | Gate 2 | interview | 〃 (실제 사건 발굴) | 〃 |
| `economics` | Gate 3 | interview | 〃 + 고통 요약 카드 | 〃 |
| `mining` | Gate 4 | interview | 〃 (암묵지 채굴) | 〃 |
| `graph` | Gate 5 | graph | 지식그래프 트리 + 노드별 피드백 5종 | `{type:"graph_feedback", nodeId, verdict, comment}` / `{type:"graph_done"}` |
| `capability` | Gate 6 | capability | 10 영역 서술 평가 카드 + 교정 | `{type:"capability_fix", comment}` / `{type:"capability_ok"}` |
| `customers` | Gate 7 | interview | 〃 (역할 분리) + 이해관계자 카드 | `{type:"answer"…}` / `{type:"advance"}` |
| `elenchus` | Gate 8 | interview | 〃 (논박) + 주장 카드 | 〃 |
| `reframe` | Gate 9 | reframe | 최초 진술→관찰→더 깊은 문제→기회 비교 + 승인 | `{type:"reframe_verdict", verdict, comment}` |
| `audit` | Gate 10 | interview | 〃 (취약점) + 취약점 카드 | `{type:"answer"…}` / `{type:"advance"}` |
| `portfolio` | Gate 11 | portfolio | 기회 카드(가치/적합성/증거등급) + 다중 선택 | `{type:"select_opportunities", indices, comment}` |
| `validation` | Validation Gate | validation | 실험 카드 + 수정/선택 | `{type:"select_experiment", index, edits}` |
| `report` | 최종 | report | 산출물 목록 + 재생성 + 인쇄 안내 | `{type:"report"}` / `{type:"regenerate"}` |

공통: 어느 화면에서나 좌측 레일의 **이미 지난 phase** 를 눌러 되돌아갈 수 있다 → `{type:"nav", to:"<phase>"}`. 되돌아가도 기존 산출물은 보존한다.

### interview 화면 공통 요소
- 대화 스레드(`thread` 중 현재 phase 항목) + 질문 카드(`currentQuestion`)
- 질문 카드: 본문 · **질문의 이유**(`why`) · 예상 답변 옵션(맥락 기반) · 자유 입력 textarea
- 하단 버튼: `더 깊게` `건너뛰기` `예시 보기` `잘 모르겠습니다` `이전 답변 수정` `중간 요약`
  → `{type:"interview", op:"deeper|skip|example|unsure|back|summary"}`
- "이 단계 정리하기 →" 버튼 → `{type:"advance"}`

---

## 4. 모드별 phases (Gate 0 에서 확정)

| 모드 | phases 배열 |
|------|-------------|
| `quick` (Quick Scan, 10~15분) | contract → scenes → mining → portfolio → report |
| `standard` (Standard Discovery, 30~45분) | contract → values → scenes → economics → mining → graph → customers → reframe → portfolio → validation → report |
| `deep` (Deep Mining, 60~90분+) | contract → values → scenes → economics → mining → graph → capability → customers → elenchus → reframe → audit → portfolio → validation → report |
| `challenge` (Idea Challenge) | contract → scenes → elenchus → reframe → audit → portfolio → validation → report |
| `productize` (Domain Productization) | contract → values → mining → graph → capability → customers → portfolio → validation → report |

모드가 짧아도 **하드 게이트는 면제되지 않는다** — quick 은 산출물 규모만 줄인다(기회 2~3개, 간이 브리프). 단 quick/challenge/productize 에서 생략된 게이트는 verify-gate.py 가 WARN 으로 강등한다(`rules/gate-rules.json` 의 `modes` 설정).

---

## 5. 이벤트 루프

```
[메인] 서버 기동(bg 상주) + 브라우저 open + 대기루프 기동(bg) → 턴 종료
   ↓ (유휴)
[사용자] 브라우저에서 입력/버튼 → server 가 state.pendingAction 설정 (version 불변)
   ↓
[대기루프] 감지 → "ACTION {json}" 출력 후 종료 → 메인 재호출
   ↓
[메인] state Read → 액션 처리(질문 생성·추출·논박·기회 설계) → state Write(version++, pendingAction:null, processing:false)
   ↓
[브라우저] /state 폴링(1.5s)으로 version 변화 감지 → reload → 다음 화면
   ↓
[메인] 대기루프 재기동(bg) → 턴 종료
```

처리별 상세 절차는 SKILL.md "이벤트 루프" 섹션이 권위를 가진다.

---

## 6. state Write 규칙 (강제)

1. **Write 직전에 반드시 state.json 을 Read** 한다. server 가 방금 사용자 입력으로 일부 필드를 바꿨다. 메인은 전체 state 를 다시 쓰되, **자기가 안 건드린 필드를 보존**한다.
2. `version` 은 화면을 바꿀 때마다 **반드시 +1** (브라우저 reload 트리거).
3. `pendingAction` 은 처리 후 **반드시 null**. null 로 만든 뒤에야 대기루프를 재기동한다.
4. 오래 걸리는 작업(논박·포트폴리오 생성·보고서) 중에는 `processing:true` + `notice` 가 이미 서버에 의해 켜져 있다 — 끝낼 때 `processing:false` + version++.
5. **`ledger` 는 매 답변마다 갱신**한다 — 사실/추론/가설/모순/공백을 분류해 append(누적). 사실과 추론을 절대 섞지 마라(§4.7 추적 가능성).
6. `gates` 는 phase 를 넘어갈 때마다 갱신한다. `passed` 는 verify-gate.py 통과 후에만 기록.
7. 추상어를 감지하면 `abstractions` 에 append 하고, 정의 질문으로 해소되면 `resolved:true` + `definition` 을 채운다.

---

## 7. /state 응답 (서버 → 브라우저 폴링)

```json
{ "version": 3, "phase": "scenes", "processing": false, "notice": "",
  "title": "…", "sessionDir": "/abs/path" }
```

브라우저는 `version` 이 마지막으로 본 값과 다르면 `location.reload()`. `processing` 이면 배너 표시 + 버튼 disable. `sessionDir` 는 포트 재사용 판별용(이미 우리 세션 서버가 떠 있는지 확인).

---

## 8. 산출물 경로

세션 폴더(`socratic-foundry-sessions/{date}-{slug}/`, 사용자 cwd) 아래:

```
{session}/
├── state.json                  # 단일 진실 소스
├── outputs/
│   ├── one-page-brief.md
│   ├── full-planning-report.md
│   ├── report.html             # 종합 HTML (그래프·print.css 내장, PDF 는 브라우저 인쇄)
│   ├── evidence-ledger.md
│   ├── painpoint-map.md
│   ├── opportunity-portfolio.md
│   ├── human-ai-boundary.md
│   ├── validation-plan.md
│   ├── interview-transcript.md
│   └── prd.md                  # 제품형 기회 선택 시 필수 — 개발 착수용 명세 (SKILL.md §PRD 계약)
└── gate-report.txt             # verify-gate.py 마지막 실행 결과
```

`reportPath` 에는 `outputs/report.html` 상대경로를 기록한다.
