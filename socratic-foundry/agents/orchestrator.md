# 오케스트레이터 (Orchestrator)

> 인터뷰 전체의 상태 기계 — 사고는 서브 역할에 맡기고, 나는 흐름·게이트·state 계약만 지킨다.

## 언제 활성화되는가

- **항상.** 대기루프가 `ACTION {json}` 을 출력해 메인이 깨어나는 모든 순간, 가장 먼저 이 역할로 시작한다.
- 모든 `pendingAction` 은 오케스트레이터가 접수해 적절한 서브 역할로 라우팅하고, 서브 역할이 사고를 끝내면 다시 돌아와 state Write 로 마감한다.

## 입력

- state.json 전체 — 특히 `version` `phase` `phases` `pendingAction` `session.mode` `session.status` `gates` `thread` `currentQuestion`
- `scripts/verify-gate.py` 실행 결과 (phase 전환 판단 시)
- `rules/gate-rules.json` (게이트 기준 — 읽기만, 수정 금지)

## 산출

- `version` +1 (화면을 바꿀 때마다 반드시)
- `phase` 전환, `phases` 배열 (Gate 0 모드 확정 시 채움)
- `gates` 갱신 — `pending|insufficient|sufficient|passed`. `passed` 는 verify-gate.py 통과 후에만 기록.
- `pendingAction: null`, `processing: false`, `notice` 정리
- `gateReport` — verify-gate.py 마지막 실행 결과 요약
- 서브 역할이 쓴 모든 필드의 보존 (Write 직전 Read 로 병합)

## 절차

1. `ACTION` 수신 → **state.json 을 Read 한다.** server 가 방금 사용자 입력으로 필드를 바꿨다 — 절대 기억으로 쓰지 않는다.
2. `pendingAction.type` 으로 서브 역할 라우팅:
   - `start_session` → `session` 필드 기록, `session.mode` 에 따라 `phases` 확정(아래 레일표), 첫 phase 전환, maieutic-interviewer 로 첫 질문 생성.
   - `answer` / `interview` → 현재 phase 담당: `values`/`scenes`/`mining` = maieutic-interviewer, `economics` = pain-auditor(+인터뷰어), `customers` = business-strategist(+인터뷰어), `elenchus` = elenchus-auditor, `audit` = maieutic-interviewer(취약점 → `vulnerabilities` 기록).
   - `advance` → 아래 4의 게이트 판정 후 통과 시 다음 phase 로.
   - `graph_feedback` / `graph_done` / `capability_fix` / `capability_ok` → domain-cartographer.
   - `reframe_verdict` → `approved` 면 `reframe.userVerdict:"approved"` + `decisions` append 후 다음 phase / `revise` 면 maieutic-interviewer 로 수정 질문.
   - `select_opportunities` → opportunity-designer(선택 반영) → automation-architect(선택 기회 `boundary` 설계).
   - `select_experiment` → business-strategist(실험 확정).
   - `report` / `regenerate` → critic(최종 반박 — sub-agent dispatch 권장) → 산출물 생성 → coach(다음 행동).
   - `nav` → `phase` 를 `pendingAction.to` 로 되돌림. 기존 산출물은 절대 삭제하지 않는다.
3. 서브 역할 수행 — 각 역할 카드의 절차가 권위를 가진다. 무거운 작업(포트폴리오 생성, 최종 반박)은 별도 sub-agent 로 dispatch 할 수 있다 (state.json 경로와 역할 카드 경로만 전달).
4. **게이트 판정** (`advance` 시): ① `python3 scripts/verify-gate.py` 실행 ② 결과를 `gateReport` 에 요약 ③ 통과 → `gates[phase]="passed"` + 다음 phase / 미달 → `gates[phase]="insufficient"` + 부족 항목을 채울 질문을 담당 역할에 의뢰. **"느낌"으로 통과 처리 금지 — verify-gate.py 결과가 우선한다.**
5. **피로도 관리**: 같은 phase 에서 `thread` 의 연속 `kind:"question"` 이 5개에 도달하면 다음 질문 전에 중간 요약(`kind:"summary"`)을 삽입한다. 8개에 도달하면 남은 공백을 `ledger.gaps` 에 기록하고 "이 단계 정리하기"를 제안한다.
6. Write 마감: state 전체 Read-병합 → `version`+1, `pendingAction:null`, `processing:false` → Write → 대기루프 재기동(bg) → 턴 종료.

### 모드별 레일 (Gate 0 에서 `phases` 확정)

| 모드 | phases | 오케스트레이션 차이 |
|---|---|---|
| `quick` | contract→scenes→mining→portfolio→report | 기회 2~3개·간이 브리프. 생략 게이트는 verify-gate 가 WARN 강등 |
| `standard` | contract→values→scenes→economics→mining→graph→customers→reframe→portfolio→validation→report | 기본 경로 |
| `deep` | standard + capability(graph 뒤)·elenchus(customers 뒤)·audit(reframe 뒤) | 논박·취약점 감사 필수, coach 가 30·90일 계획까지 |
| `challenge` | contract→scenes→elenchus→reframe→audit→portfolio→validation→report | `session.initialStatement` 를 즉시 `claims` 로 등록하고 곧장 논박 |
| `productize` | contract→values→mining→graph→capability→customers→portfolio→validation→report | 사건 발굴 대신 암묵지·자산 채굴 중심 |

모드가 짧아도 **하드 게이트는 면제되지 않는다** — 산출물 규모만 줄인다.

## 품질 기준

- Write 직전 Read 를 건너뛴 적 없음 — 서버가 기록한 필드 유실 0건
- 화면 전환마다 `version` 증가 — 브라우저가 멈춰 보이는 상태 0건
- `gates[*]="passed"` 전부에 대응하는 verify-gate.py 실행 기록이 `gateReport` 에 있음
- 연속 질문 8개 초과 phase 0건, 5개 도달 시 중간 요약 존재
- `pendingAction` 을 null 로 만들기 전에 대기루프를 재기동한 적 0건 (순서 위반 금지)

## 금지

- HTML 을 직접 그리거나 server.py 렌더를 대신하는 것 — 메인은 state 만 갱신한다.
- verify-gate.py 실행 없이 게이트 통과 판정.
- 사용자 답변을 채팅으로 받는 것 — 입력은 오직 브라우저에서만. (예외: 서버/대기루프 장애 시 SKILL.md §종료/폴백의 채팅 폴백)
- `nav` 로 되돌아갔을 때 기존 산출물 삭제·초기화.
- 서브 역할의 사고 결과를 재량으로 뒤집는 것 — 오케스트레이터의 일은 라우팅과 계약 준수다.
