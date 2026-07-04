# 산파술 질문 생성 규칙 — currentQuestion 설계 실행 지침

모든 인터뷰형 phase(`values`·`scenes`·`economics`·`mining`·`customers`·`elenchus`·`audit`)에서
메인 Claude가 다음 질문을 만들 때 따르는 규칙이다. 산파는 답을 낳게 하는 사람이지, 답을 주는 사람이 아니다.

---

## 1. 대원칙

1. **개수가 아니라 방향.** 좋은 인터뷰는 질문이 많은 인터뷰가 아니라, 진술에서 출발해
   **진술 → 근거 → 판단 기준 → 예외 → 의미 → 가치 → 사업 기회**로 파고드는 인터뷰다.
   직전 답변이 어느 단계인지 판단하고, 다음 단계로 내려가는 질문을 만든다.
2. **한 번에 하나.** `currentQuestion`은 항상 질문 1개만 담는다. "그리고", "또한"으로 두 질문을 잇지 않는다.
3. **모든 질문에 `why` 필수.** 이 질문이 왜 필요한지 한 문장으로 쓴다. why를 못 쓰겠으면 그 질문은 버린다.
4. **options는 맥락 기반 2~4개.** 직전 답변·도메인 지식·해당 업계의 경쟁 패턴에서 추론한
   구체적 예상 답변을 `{ "label", "hint" }`로 만든다. "① 매우 그렇다 ② 그렇다…" 식 추상적 4지선다 금지.
   사용자가 옵션 밖의 답을 쓸 수 있도록 자유 입력은 항상 열려 있다(서버가 렌더).
5. **답변을 받으면 먼저 분류.** 답변 내용을 사실/추론/가설로 나눠 `ledger`에 append 한 뒤에 다음 질문을 만든다(§6 Write 규칙).

```json
{ "text": "그 병합 작업, 가장 최근에는 언제 했고 몇 시간 걸렸습니까?",
  "why": "'힘들다'는 진술을 측정 가능한 사건으로 바꾸기 위해서입니다.",
  "gate": "scenes",
  "options": [
    { "label": "지난주 금요일, 3시간쯤", "hint": "정기 업무였다면" },
    { "label": "이번 달엔 안 했다", "hint": "빈도가 불규칙하다면" }
  ],
  "inputType": "text", "allowSkip": true, "allowExample": true, "allowUnsure": true }
```

---

## 2. 추상어 감지

아래 단어가 답변에 나오면 그냥 넘어가지 않는다:

> 편리한 / 혁신적인 / 자동화 / 누구나 / 전문가 / 플랫폼 / 효율적 / 맞춤형 / 커뮤니티 / AI 기반 / 고품질 / 확장 가능한

절차:
1. `abstractions[]`에 append: `{ "term":"자동화", "context":"출결을 자동화하고 싶다", "resolved":false, "definition":"" }`
2. 정의 질문을 던진다: "'쉽다'는 것은 사용자가 어떤 행동을 하지 않아도 된다는 뜻입니까?"
3. 정의가 나오면 `resolved:true` + `definition`을 채운다. 정의 없이 같은 단어가 3번째 등장하면 진행을 멈추고 정의부터 받는다.

---

## 3. 6가지 감지 → 질문 패턴

| 감지 | 신호 | 던지는 질문 (예) | 기록 |
|------|------|------------------|------|
| **추상어** | §2 목록 단어 | "'쉽다'는 사용자가 어떤 행동을 하지 않아도 된다는 뜻입니까?" | `abstractions[]` |
| **해결책 집착** | 문제보다 "SaaS로", "앱으로"가 먼저 나옴 | "SaaS 형태는 잠시 내려놓고, 가장 최근에 이 문제를 실제로 겪은 장면부터 들려주십시오." | `thread` probe, 장면은 `events[]` |
| **증거 부족** | "다들 원한다", "분명히 필요하다" | "실제로 이 문제를 말한 사람은 몇 명이며, 최근에 어떤 표현을 썼습니까?" | 답이 사건이면 `ledger.facts`, 아니면 `ledger.hypotheses` + `ledger.gaps` |
| **도메인 자산** | "그건 보면 안다", "감으로" | "그 판단을 할 때 무의식적으로 확인하는 신호 3가지는 무엇입니까?" | `judgmentRules[]` (domain-mining.md) |
| **모순** | 이전 발언과 충돌 | "A와 B가 동시에 성립하려면, 양쪽을 나눌 기준이 필요합니다. 그 기준은 무엇입니까?" | `ledger.contradictions` |
| **지나친 자동화** | "전부 자동으로", "사람 없이" | "잘못된 판단이 나갔을 때 피해를 되돌릴 수 있습니까? 최종 책임은 누가 집니까?" | `boundary[]` 후보, 필요시 `vulnerabilities[]` |

---

## 4. 진술보다 사건

- 약한 증거: "힘들다", "시간이 많이 든다" — 형용사만 있는 진술.
- 강한 증거: "매주 금요일 3시, 여섯 지점 파일 병합에 3시간" — 시각·대상·소요가 있는 사건.

진술을 받으면 사건으로 바꾸는 질문을 던지고, 확보한 사건은 `events[]`에 기록한다.

**사건 확보 체크리스트** (`events[]` 필드와 1:1):

| 확인할 것 | 필드 |
|-----------|------|
| 언제 (가장 최근 그 일이 있었던 날) | `when` |
| 무엇을 하다가 | `doing` |
| 누구와, 어떤 도구로 | `actors`, `tools` |
| 어디서 시간이 갔나 / 막혔나 | `stuckAt`, `timeTaken` |
| 어떤 임시방편을 썼나 | `workaround` |
| 무엇을 포기했나 | `gaveUp` |

당시 했던 말·들었던 말을 그대로 `quote`에 담으면 최상급 증거다. Gate 2 통과에는 사건 최소 2개.

---

## 5. 게이트별 질문 뱅크

그대로 읽지 말고, 직전 답변의 단어를 넣어 변형해 쓴다.

### Gate 1 — values (`values` phase)
- "어떤 방식으로 일하고 싶습니까? 하루가 어떻게 흘러가면 좋은 하루입니까?" → `workStyle`
- "돈·자율성·안정성·영향력·성장 — 중요한 순서로 늘어놓는다면?" → `priorities` (inputType은 options 다중 선택 활용 가능)
- "절대 하고 싶지 않은 사업 방식은 무엇입니까?" → `antiGoals`
- "많은 고객을 얕게 만나는 쪽과 적은 고객을 깊게 만나는 쪽, 어느 쪽입니까?" → `customerDepth`
- "혼자 하는 그림입니까, 팀을 꾸리는 그림입니까?" → `teamPreference`
- "1년 뒤 '성공했다'고 스스로 인정할 최소 조건은 무엇입니까?" → `successMinimum`

### Gate 2 — scenes (`scenes` phase) : 최근 장면 6문
1. "가장 최근에 그 문제를 겪은 게 언제입니까?"
2. "그때 정확히 무엇을 하던 중이었습니까?"
3. "누구와 함께, 어떤 도구를 쓰고 있었습니까?"
4. "어디서 시간이 가장 많이 샜습니까?"
5. "어떤 임시방편으로 넘겼습니까?"
6. "그것 때문에 결국 포기한 일은 무엇입니까?"

### Gate 3 — economics (`economics` phase)
- "그 일은 월에 몇 번 일어납니까?" → `pains[].frequencyPerMonth`
- "한 번에 몇 시간을 먹습니까?" → `hoursPerOccurrence`
- "실수가 나면 비용이 얼마나 듭니까? 최근 사례는?" → `errorCost`
- "이 문제를 줄이려고 이미 쓴 돈(도구·외주·인력)이 있습니까?" → `alreadyPaid`
- "이 문제가 내일 사라진다면, 그 시간과 에너지로 무엇을 더 하겠습니까?" → `unlockedIfSolved`

### Gate 7 — customers (`customers` phase)
- "아파하는 사람과 돈을 내는 사람이 같은 사람입니까?" → `stakeholders.buyerIsSufferer`
- "구매를 승인하는 사람은 따로 있습니까?" → `approver`
- "이게 도입되면 오히려 일이 늘어나는 사람은 누구입니까?" → `operator` / `blocker`
- "기존 방식이 유지될 때 이익을 보는 사람은 누구입니까?" → `statusQuoWinner`
- "첫 번째 고객이 될 사람의 이름을 댈 수 있습니까?" → `firstCustomer`, `accessPath`

### Gate 10 — audit (`audit` phase)
- "이 사업이 실패한다면 가장 가능성 높은 이유는 무엇입니까?" → `vulnerabilities[]`
- "당신이 한 달을 쉬면 이 사업은 멈춥니까?" → 운영 의존 취약점
- "고객 1명을 설득하는 데 시간과 돈이 얼마나 듭니까?" → 고객 접근 취약점
- "경쟁자가 복제할 수 없는 것은 무엇입니까?" → `assets[]` 대조
- "아직 검증 안 된 것 중 가장 위험한 전제는 무엇입니까?" → `isRiskiestAssumption:true`, `experiments[]` 후보

---

## 6. 피로도 관리

- **중간 요약**: 연속 질문 5~8개마다 지금까지의 사실·추론을 3~5줄로 요약해 `thread`에 `kind:"summary"`로 append 하고 확인을 받는다. 요약은 오해를 조기에 잡는 장치다.
- **속도 조절**: 답변이 눈에 띄게 짧아지면(한 줄 이하 연속 2~3회) 질문 밀도를 낮춘다 — options 중심의 가벼운 질문으로 전환하거나 "이 단계 정리하기"를 제안한다.
- **"잘 모르겠습니다"** (`op:"unsure"`): 즉시 구체적 예시 2~3개를 제시하고 재질문하거나, 그래도 없으면 `ledger.gaps`에 미확인 항목으로 기록하고 통과한다. 모르는 것을 억지로 답하게 하면 가설이 사실로 둔갑한다.
- **되돌아가기** (`op:"back"`): 이전 답변 수정 요청이 오면 관련 `ledger` 항목·`events`를 함께 갱신한다. 수정 전 내용을 덮어쓰되, 그 수정으로 무효가 된 추론(`inferences.basis`)이 있는지 확인한다.

---

## state 기록 요약

| 무엇을 | 어느 필드에 |
|--------|-------------|
| 지금 던지는 질문 (1개, 이유 포함) | `currentQuestion` (`text`, `why`, `gate`, `options`, `inputType`) |
| 질문·답변·중간 요약의 흐름 | `thread[]` (`role`, `content`, `kind:"question"\|"answer"\|"summary"\|"probe"`, `phase`) |
| 감지한 추상어와 그 정의 | `abstractions[]` (`term`, `context`, `resolved`, `definition`) |
| 답변 속 사실/추론/가설/공백 | `ledger.facts` / `ledger.inferences` / `ledger.hypotheses` / `ledger.gaps` |
| 발언 간 충돌 | `ledger.contradictions` |
| 확보한 실제 사건 | `events[]` (`when`, `doing`, `actors`, `tools`, `stuckAt`, `timeTaken`, `workaround`, `gaveUp`, `quote`) |
| Gate 1 답변 | `values` (`workStyle`, `priorities`, `antiGoals`, `customerDepth`, `teamPreference`, `successMinimum`) |
| Gate 3 답변 | `pains[]` 각 비용 필드 (painpoint-taxonomy.md) |
| Gate 7 답변 | `stakeholders` 각 필드 |
| Gate 10 답변 | `vulnerabilities[]`, `experiments[]` 후보 |
