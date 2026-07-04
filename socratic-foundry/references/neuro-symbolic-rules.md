# 뉴로심볼릭 분리 + 추적 가능성 — 기록 규율 실행 지침

Socratic Foundry의 신뢰성은 두 가지에서 나온다: **역할 분리**(생각하는 층과 검증하는 층을 섞지 않음)와
**추적 가능성**(모든 주장이 근거 ID로 거슬러 올라감). 이 문서는 메인 Claude가 매 턴 지키는 기록 규율이다.

---

## 1. 역할 분리 — 누가 무엇을 하는가

### 신경망 영역 (LLM = 메인 Claude)
자연어 이해 / 답변 요약 / 패턴 발견 / 질문 생성 / 기회 발산 / 문서 작성.
잘하는 것: 유연한 해석과 발산. 못 믿을 것: 일관성 유지, 규칙 준수의 자가 판정.

### 심볼릭 영역 (server.py, scripts/verify-gate.py, rules/*.json)
- 게이트 통과 조건 판정 (사건 ≥2, 규칙 ≥3 등 — `rules/gate-rules.json`)
- 사실·추론·가설 구분 강제 (`ledger` 스키마)
- 모순 검사 (`ledger.contradictions`의 open 잔존 여부)
- 증거 추적 (산출물 주장 → 근거 ID 연결 검사)
- 고객·구매자 분리 확인 (`stakeholders.buyerIsSufferer` 미확인 차단)
- 점수 계산 규율 (`valueScore`·`fitScore` 근거 필드 존재 검사)
- 자동화 금지 규칙 (`boundary`의 `automation_forbidden` 위반 검사)
- 필수 질문 누락 검사 / 보고서 품질 검증

**철칙**: 메인은 게이트 통과를 "느낌"으로 판정하지 않는다 — verify-gate.py 결과가 우선한다.
server는 사고 작업을 하지 않는다. 이 경계를 흐리는 순간 시스템 전체가 그럴듯한 소설 생성기가 된다.

---

## 2. 5분류 표식 — 모든 정보는 다섯 중 하나다

| 분류 | 정의 | 기록 위치 |
|------|------|-----------|
| **사실** | 사용자가 제공했거나 자료로 확인됨 | `ledger.facts` — `{ "id":"F1", "content":"…", "source":"scenes#3" }` (`source`는 발화 위치·자료 출처) |
| **추론** | 여러 사실을 연결해 도출 | `ledger.inferences` — `{ "id":"I1", "content":"…", "basis":["F1","F3"] }` (`basis` 없는 추론 금지) |
| **가설** | 검증이 필요한 짐작 | `ledger.hypotheses` — `{ "id":"H1", "content":"…", "testedBy":"X1" }` (실험 연결 전이면 빈 문자열) |
| **제안** | AI가 만든 추천 선택지 — 사용자가 아직 고르지 않음 | `opportunities[]`(`selected:false`) / `experiments[]`(`selected:false`) / `graph.nodes`(`status:"proposed"`) / `currentQuestion.options` |
| **결정** | 사용자가 승인·선택함 | `decisions[]` — `{ "id":"D1", "decision":"…", "phase":"reframe", "basis":"…" }` |

전이 규칙: 가설은 실험(`experiments`)이나 새 사실로만 사실로 승격된다. 제안은 사용자 액션
(`select_opportunities`·`reframe_verdict` 등)으로만 결정이 된다. **AI가 스스로 승격시키는 경로는 없다.**

### ID 규칙

| 접두사 | 대상 | 접두사 | 대상 |
|--------|------|--------|------|
| F | ledger.facts | N | graph.nodes |
| I | ledger.inferences | CL | claims |
| H | ledger.hypotheses | V | vulnerabilities |
| C | ledger.contradictions | O | opportunities |
| E | events | X | experiments |
| P | pains | D | decisions |
| R | judgmentRules | A | assets |

접두사 + 순번(F1, F2, …). 순번은 재사용하지 않는다(철회돼도 결번 유지). 모든 교차 참조는 이 ID로 한다.

### 산출물 근거 연결

outputs/의 모든 문서에서 **주장 문장에는 근거 ID를 붙인다**:

> "학원장은 주당 3시간을 지점 데이터 병합에 쓴다 (F4, E2). 따라서 병합 자동화는 월 12시간의 가치가 있다 (I3 ← F4, F7)."

ID를 붙일 수 없는 문장이 있으면 그 문장은 가설이다 — H-ID를 만들어 붙이거나 문장을 지운다.

---

## 3. 금지 (위반 시 산출물 신뢰 전체가 무너진다)

1. **AI 추론을 사용자 사실처럼 기록 금지.** 사용자가 안 한 말을 `ledger.facts`에 넣지 않는다. AI의 연결은 반드시 `ledger.inferences` + `basis`.
2. **근거 없는 시장 규모 금지.** "국내 학원 시장 5조 원" 같은 수치는 사용자가 제시했거나 출처가 확인된 경우에만, `source`와 함께 기록한다. 그 외에는 쓰지 않는다 — 빈칸이 지어낸 숫자보다 낫다.
3. **증거 없는 수치 금지.** 전환율·이탈률·"10배 빨라진다" 류를 발명하지 않는다. 수치가 필요한 자리에 증거가 없으면 "미확인 (`gaps`)"이라고 쓴다.

---

## 4. verify-gate.py — 실행 시점과 결과 해석

### 실행 시점 (3곳, 생략 불가)

| 시점 | 이유 |
|------|------|
| **reframe 진입 전** | 재정의는 그때까지의 사실·모순 위에 선다. open 모순, 증거 없는 핵심 주장을 안고 재정의하면 그럴듯한 거짓 서사가 나온다 |
| **portfolio 확정 전** | 기회의 점수·등급이 규율(근거 필드, 자산 연결)을 지켰는지, 시간축이 실제로 분산됐는지 기계 검사 |
| **report 생성 전** | 산출물에 들어갈 주장의 근거 연결·게이트 충족을 최종 검사 |

실행: `python scripts/verify-gate.py` (기준은 `rules/gate-rules.json`). 결과 요약은 `gateReport`에,
전문은 세션 폴더 `gate-report.txt`에 기록한다.

### 결과 해석

- **FAIL** — 통과 불가. 해당 phase로 돌아가 부족분을 채운다. 메인의 판단으로 FAIL을 무시하고 진행하는 것은 절대 금지. 사용자가 "그냥 넘어가자"고 해도 무엇이 왜 FAIL인지 고지하고, 그래도 진행하면 그 사실을 `decisions[]`에 D-ID로 기록하고 산출물에 한계로 명시한다.
- **WARN** — 사용자에게 고지 후 진행 가능. quick/challenge/productize 모드에서 생략된 게이트는 WARN으로 강등된다(`rules/gate-rules.json`의 `modes`). WARN 내용은 `notice`와 최종 보고서의 한계 섹션에 남긴다.
- **PASS** — `gates`의 해당 phase 값을 `passed`로 갱신한다. `passed`는 verify-gate.py 통과 후에만 기록한다.

---

## 5. 매 턴 기록 체크 (state Write 직전)

1. 이번 답변에서 사실/추론/가설을 분리해 `ledger`에 append 했는가? (사실과 추론을 섞지 않았는가)
2. 새 추론에 `basis`(F-ID 배열)가 있는가?
3. AI가 만든 제안에 `selected:false` 또는 `status:"proposed"`가 붙어 있는가?
4. 사용자의 선택을 `decisions[]`에 D-ID로 남겼는가?
5. 모르는 것을 아는 것처럼 쓰지 않았는가? (`gaps`에 남겼는가)

---

## state 기록 요약

| 무엇을 | 어느 필드에 |
|--------|-------------|
| 사용자 제공·자료 확인 정보 | `ledger.facts` (F-ID, `source`) |
| 사실들을 연결한 AI의 도출 | `ledger.inferences` (I-ID, `basis`) |
| 검증 필요한 짐작 | `ledger.hypotheses` (H-ID, `testedBy`) |
| 발언 간 충돌 | `ledger.contradictions` (C-ID, `status`) |
| 미확인 질문·지식 공백 | `ledger.gaps` |
| AI의 추천 선택지 (미승인) | `opportunities[]`·`experiments[]` (`selected:false`), `graph.nodes` (`status:"proposed"`) |
| 사용자 승인·선택 | `decisions[]` (D-ID, `phase`, `basis`) |
| 게이트 기계 검사 결과 | `gates` (phase별 상태), `gateReport`, `gate-report.txt` |
| WARN 고지 문구 | `notice` + 보고서 한계 섹션 |
