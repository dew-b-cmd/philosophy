# 기회 주조 + 평가 + 해결 형태 — portfolio phase 실행 지침

`portfolio` phase(Gate 11)에서 발굴된 고통·판단 규칙·자산을 사업 기회(`opportunities`)로
주조하고, 인간-AI 업무 경계(`boundary`)까지 설계하는 지침이다.
기회는 AI의 **제안**이다 — `selected:false`로 만들고, 선택은 사용자가 한다.

---

## 1. 12 사업 형태 (`opportunities[].form`)

| form | 1줄 정의 | 적합 조건 |
|------|----------|-----------|
| 컨설팅 | 전문가가 고객별 문제를 직접 진단·해결 | 문제 구조가 고객마다 다르고 `judgmentRules`가 강할 때. 즉시 수익 가능 |
| 진단 서비스 | 표준화된 점검 절차로 상태·위험을 평가해 리포트 제공 | 판단 기준을 체크리스트로 만들 수 있고 반복 수요가 있을 때 |
| 교육 상품 | 강의·워크숍·코칭으로 고객이 스스로 해결하게 함 | 고객이 역량 내재화를 원하고 반복 학습 구조가 가능할 때 |
| 템플릿·콘텐츠 | 문서·체크리스트·사례집 등 자산을 상품화 | `assets[].kind:"materials"|"data"`가 이미 쌓여 있을 때 |
| 서비스형 자동화 | 고객은 결과만 받고, 내부는 사람+도구로 처리 | 수요는 확인됐지만 예외가 많아 완전 자동화가 이를 때 |
| 내부 업무 도구 | 특정 조직의 반복 업무를 코드로 해결 | 고통이 명확한 1~2개 조직과 접점이 있을 때 (첫 사례 축적용) |
| AI 에이전트 | LLM이 다단계 판단·도구 사용으로 업무 수행 | 상황이 가변적이되 판단 규칙을 프롬프트화할 수 있고 인간 개입 지점이 설계될 때 |
| 버티컬 SaaS | 특정 업종의 반복 문제를 셀프서비스 소프트웨어로 | 다수 고객이 같은 문제를 겪고 지속 사용 이유가 있을 때 (가장 무겁고 느린 형태) |
| 데이터 상품 | 축적 데이터를 리포트·API·벤치마크로 판매 | `replicability:"hard"`인 데이터 자산이 있을 때 |
| 커뮤니티 | 같은 문제를 가진 사람들의 유료 네트워크 운영 | 타인이 이미 모여드는 신뢰 자산(`kind:"trust"`)이 있을 때 |
| 플랫폼 | 공급자와 수요자를 중개 | 양쪽 모두에 접근성이 있을 때만. 초기 창업자에게 대부분 부적합 — 안이한 기본값 금지 |
| 전략적 운영 모델 | 기존 사업의 구조 자체를 바꾸는 운영 방식 판매 | 도메인 전문성 + 운영 능력이 모두 검증됐을 때 |

---

## 2. 5 시간축 (`opportunities[].horizon`) — 최소 5개, 서로 다른 시간축

| horizon | 이름 | 정의 |
|---------|------|------|
| `now` | 즉시 수익형 | 현재 역량으로 이번 달에 바로 판매 가능 (컨설팅·진단이 단골) |
| `product` | 표준 상품형 | 반복 경험을 템플릿·패키지로 표준화해 판매 |
| `automation` | 자동화형 | 판단 규칙 일부를 AI·코드로 옮겨 원가를 낮춤 |
| `scale` | 확장형 | 셀프서비스 SaaS 등 사용자 수와 무관한 구조 |
| `option` | 장기 옵션형 | 데이터·커뮤니티·플랫폼 — 지금 심어 나중에 수확 |

**규칙**: `opportunities[]`는 최소 5개, horizon이 최소 4종 이상 분산돼야 한다. 전부 `scale`이면
"모든 문제의 SaaS화" 금지 위반(interview-ethics.md)이다. `now`가 하나도 없으면 사용자의 생계 축이 없다 — 반드시 1개 이상 설계한다.
앞 시간축의 산출(사례·데이터·신뢰)이 뒤 시간축의 입력이 되도록 `assetBuilt` → `requiredAssets` 사슬을 잇는다.

---

## 3. 평가 — valueScore / fitScore / evidenceGrade

### 잠재 가치 `valueScore` 1~5 (`valueWhy`에 근거 서술)
문제 크기 / 빈도 / 지불 가능성 / 반복 수익 구조 / 확장성을 종합. `pains[]`의 실측치(P-ID)를 인용해야 한다.

### 창업자 적합성 `fitScore` 1~5 (`fitWhy`에 근거 서술)
도메인 전문성(`judgmentRules`) / 비대칭 자산(`assets`) / 고객 접근성(`stakeholders.accessPath`) /
실행 능력(`capabilities`) / 개인 가치 적합(`values.antiGoals` 위반 여부 — 위반하면 점수와 무관하게 명시).

### 증거 등급 `evidenceGrade` (`gradeWhy`에 근거 서술)

| 등급 | 기준 |
|------|------|
| A | 결제·반복 사용이 확인됨 |
| B | 실제 문제·반복 행동이 확인됨 (`events` 2개+, `alreadyPaid` 존재 등) |
| C | 사례·인터뷰는 있으나 지불 미확인 |
| D | 추정·AI 가설 |
| E | 근거 없음 |

**표현 규율**: 점수와 등급은 항상 함께, 등급이 낮으면 낮다고 말한다 —
"잠재 가치 5 / 적합성 4 / 증거 D — 매력적이지만 지불 의사 검증이 우선입니다."
높은 점수가 낮은 등급을 가리게 하지 않는다. D/E 기회의 `biggestRisk`는 대개 그 자체로 `experiments[]`의 대상이다.

---

## 4. 해결 형태 선택 기준

같은 고통도 형태를 잘못 고르면 죽는다. 형태별 성립 조건:

- **자동화** — 입출력이 명확 / 고빈도 / 규칙을 설명 가능(`judgmentRules`가 이미 문장화됨) / 오류를 사람이 검수 가능.
- **AI 에이전트** — 다단계 계획·도구 사용이 필요 / 상황이 가변적 / 판단·예외 처리가 핵심 / 인간 개입 지점을 설계할 수 있음.
- **SaaS** — 다수 고객이 동일 문제를 반복 / 셀프서비스로 온보딩 가능 / 맞춤 요구가 제한적 / 지속 사용할 이유가 있음.
- **컨설팅** — 문제 구조가 고객마다 다름 / 전문가 진단이 가치의 핵심 / 표준화가 어려움.
- **교육** — 고객이 직접 해결할 역량을 원함 / 반복 학습 구조 / 템플릿·사례 제공 가능.
- **서비스형 자동화** — 고객은 결과를 원함 / 예외가 많음 / 완전 자동화 전에 수요부터 검증해야 함. (SaaS로 가기 전 기본 경유지)

판단 재료는 `pains[].frequencyPerMonth`(빈도), `judgmentRules[].exceptions`(예외 밀도),
`stakeholders`(셀프서비스 가능성)에서 가져온다. 예외가 많은데 자동화를 제안하고 있다면 형태를 다시 고른다.

---

## 5. 인간-AI 경계 6모드 (`boundary[]`)

기회마다 핵심 업무를 쪼개 모드를 배분한다. 배분 기준 4가지:
**가역성**(잘못되면 되돌릴 수 있는가) / **책임 소재**(누가 책임지는가) / **판단 필요**(규칙으로 못 덮는 판단인가) / **가치 판단 여부**(옳고 그름·우선순위의 문제인가).

| mode | 뜻 |
|------|----|
| `ai_only` | AI 단독 수행 (가역적·규칙적·저위험) |
| `ai_draft_human_review` | AI 초안 → 인간 검토 후 확정 |
| `human_decide_ai_execute` | 인간이 결정, AI가 실행 |
| `co_work` | 인간과 AI가 실시간 협업 |
| `human_only` | 인간 전담 (가치 판단·관계·책임) |
| `automation_forbidden` | 자동화 자체를 금지 (사용자가 선언, 번복은 사용자만) |

예시 배분:

| task | mode | reason |
|------|------|--------|
| 고객 요구 수집 인터뷰 | `co_work` | 신뢰 형성은 인간, 기록·정리는 AI |
| 데이터 정리·병합 | `ai_only` | 가역적이고 규칙 명확 |
| 고객 우선순위 결정 | `human_only` | 가치 판단, 결과 책임이 사용자에게 |
| 기획서 초안 작성 | `ai_draft_human_review` | 초안은 AI가 빠르나 확정 책임은 인간 |
| 법률·윤리 관련 판단 | `human_only` + `automation_forbidden` | 비가역·책임 소재가 사용자 |
| 확정된 안내 메일 발송 | `human_decide_ai_execute` | 결정은 인간, 반복 실행은 AI |

기록: `{ "task":"…", "mode":"…", "reason":"…" }`. `reason`에는 배분 기준 4가지 중 무엇이 결정적이었는지 쓴다.
elenchus의 consequence 검토, audit의 자동화 위험에서 나온 항목을 반드시 반영한다.

---

## 6. opportunities[] 기록 지침 — 전 필드

```json
{ "id": "O1", "horizon": "now", "form": "진단 서비스",
  "name": "학원 운영 데이터 건강검진",
  "pitch": "출결·상담 데이터를 반나절 안에 진단해 새는 돈 3곳을 짚어주는 리포트",
  "targetCustomer": "지점 3개 이상 학원 원장", "buyer": "원장 본인",
  "valueScore": 4, "valueWhy": "P1 월 12시간 손실 + P2 이탈 위험 (F4, F7)",
  "fitScore": 5, "fitWhy": "R1~R3 판단 규칙 + A1 5년치 상담 데이터, accessPath 확보됨",
  "evidenceGrade": "C", "gradeWhy": "불만 사례 3건 확인, 지불 의사는 미확인",
  "whyBuy": "시간 절약이 아니라 '어느 지점이 새는지'를 처음으로 숫자로 봄 (P1.unlockedIfSolved)",
  "assetBuilt": "진단 사례 리포트 축적 → O3 자동화형의 학습 데이터",
  "requiredAssets": ["A1"],
  "biggestRisk": "원장이 진단 결과를 보고도 행동하지 않을 위험",
  "whyYou": "동일 판단을 30건 이상 반복한 이력 (R1.evidence), 경쟁자는 데이터 접근 불가 (A1 replicability:hard)",
  "selected": false }
```

- `whyBuy` — 고객의 구매 이유. **시간 절약 이외의 가치**를 반드시 포함 (`pains[].unlockedIfSolved` 인용).
- `assetBuilt` — 이 기회를 실행하면 축적되는 자산(데이터/사례/신뢰). 다음 horizon과의 연결 고리.
- `whyYou` — 다른 사람이 아닌 이 사용자여야 하는 이유. `judgmentRules`·`assets`의 ID 인용. 못 쓰겠으면 fitScore를 다시 본다.
- `biggestRisk` — 가장 큰 위험 1개. `vulnerabilities[]`와 연결되고, 선택된 기회의 리스크는 `experiments[]`의 `riskiestAssumption`이 된다.
- 모든 근거 서술(`valueWhy`·`fitWhy`·`gradeWhy`·`whyYou`)에는 ID를 인용한다. ID 없는 근거는 가설 취급.

제시 후 `{type:"select_opportunities"}` 액션으로 사용자가 고르면 해당 항목 `selected:true` + `decisions[]`에 D-ID 기록.

---

## state 기록 요약

| 무엇을 | 어느 필드에 |
|--------|-------------|
| 기회 1건 (AI 제안) | `opportunities[]` (`id`:O, `horizon`, `form`, `name`, `pitch`, `targetCustomer`, `buyer`, `selected:false`) |
| 평가 3축과 근거 | `valueScore`/`valueWhy`, `fitScore`/`fitWhy`, `evidenceGrade`/`gradeWhy` |
| 구매 이유·축적 자산·창업자 근거·최대 위험 | `whyBuy`, `assetBuilt`, `whyYou`, `biggestRisk` |
| 필요한 비대칭 자산 연결 | `requiredAssets` (A-ID 배열) |
| 인간-AI 업무 배분 | `boundary[]` (`task`, `mode`, `reason`) |
| 사용자의 기회 선택 | `opportunities[].selected:true` + `decisions[]` (D-ID) |
| 선택된 기회의 최대 위험 → 실험 | `experiments[]` (`riskiestAssumption`) |
| 점수 근거가 부족한 항목 | `ledger.gaps` (검증 대상) |
