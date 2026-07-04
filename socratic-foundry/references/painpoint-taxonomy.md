# 고통의 경제성 — pains 분석 실행 지침

`economics` phase(Gate 3)에서 사건(`events`)을 경제적으로 측정 가능한 고통(`pains`)으로
변환하는 작업 지침이다. "불편하다"는 사업의 근거가 못 된다. "월 12회 × 3시간 × 실수 시 80만 원"이 근거다.

---

## 1. 분석 항목 10종 — pains[] 필드와 1:1 매핑

각 고통(`pains[]` 항목)마다 아래 10개 항목을 확인한다. 반드시 사용자가 말한 수치·사례만 기록한다 —
사용자가 모르면 0이나 빈 문자열로 두고 `ledger.gaps`에 남긴다. AI가 추정치를 채워 넣지 않는다.

| # | 분석 항목 | 캐는 질문 | 필드 |
|---|-----------|-----------|------|
| 1 | 발생 빈도 | "월에 몇 번 일어납니까?" | `frequencyPerMonth` (숫자) |
| 2 | 소요 시간 | "한 번에 몇 시간을 먹습니까?" | `hoursPerOccurrence` (숫자) |
| 3 | 직접 비용 | "이 일에 직접 나가는 돈(인건비·도구·외주)은?" | `directCost` |
| 4 | 오류·재작업 | "실수가 나면 무엇을 다시 해야 하고 얼마가 듭니까?" | `errorCost` |
| 5 | 의사결정 지연 | "이것 때문에 미뤄지는 결정이 있습니까? 미뤄지면?" | `delayCost` |
| 6 | 고객 이탈 | "이 문제로 떠난(떠날 뻔한) 고객이 있습니까?" | `churnRisk` |
| 7 | 매출 기회 손실 | "이것 때문에 못 잡은 주문·계약이 있습니까?" | `revenueLoss` |
| 8 | 품질 저하 | "이 문제가 결과물 품질에 어떤 흔적을 남깁니까?" | `qualityRisk` |
| 9 | 법적·보안 위험 | "잘못되면 규정 위반·유출·분쟁으로 번질 수 있습니까?" | `legalRisk` |
| 10 | 감정적 피로 | "이 일이 있는 날과 없는 날, 퇴근할 때 기분이 다릅니까?" | `emotionalLoad` |

공통 필드:
- `eventIds` — 이 고통의 근거가 된 사건 ID(E-ID). **사건 없는 고통은 등록하지 않는다.**
- `description` — 고통 한 줄 서술 (사건의 언어를 유지: "매주 금요일 여섯 지점 파일 병합").
- `alreadyPaid` — 이 문제를 줄이려고 **이미 쓴 돈** (도구 구독·외주·알바). 이미 지불한 이력은 지불 의사의 가장 강한 선행 증거다 → `ledger.facts`에도 F-ID로 올린다.
- `severityNote` — 종합 심각도 한 줄 (수치가 아니라 정성 비교의 결과, §4).

10개를 전부 심문하듯 묻지 않는다 — 1·2번은 필수, 나머지는 사건의 성격에 맞는 3~4개를 골라 판다.
해당 없는 항목은 빈 문자열로 둔다.

---

## 2. 가짜 문제 제거

아래 셋 중 하나에 걸리면 `pains[]`에 올리지 않거나, 올렸더라도 `severityNote`에 명시하고 기회의 근거에서 뺀다:

1. **한 번뿐인 불편** — `frequencyPerMonth`가 사실상 0. 연 1회 이벤트는 사업의 심장이 못 된다.
2. **이미 좋은 대안이 있는 불편** — "그 도구를 왜 안 씁니까?"에 납득할 답이 없으면 가짜. 대안의 존재는 `ledger.facts`에 기록.
3. **회피 행동이 없는 불편** — 말로는 아프다는데 임시방편도, 검색도, 지출도(`workaround`·`alreadyPaid` 전부 빈 값) 없으면 아직 안 아픈 것이다. "정말 아픈 문제는 흔적을 남긴다."

가짜로 판정한 이유는 사용자에게 그대로 말한다. 판정 근거가 부족하면 `ledger.gaps`에 남기고 보류한다.

---

## 3. 효율성보다 효과성 — unlockedIfSolved

"시간 절약"은 고통 분석의 가장 낮은 층이다. 시간을 아껴서 **무엇이 가능해지는가**까지 내려가야
기회의 `whyBuy`(구매 이유)가 나온다. 반드시 묻는다:

> "이 문제가 내일 사라진다면, 그 시간과 에너지로 무엇을 더 하겠습니까?"

답을 `unlockedIfSolved`에 기록한다. 층위가 높을수록 강한 기회다:

| 층위 | 예 |
|------|----|
| 시간 절약 (최하) | "3시간 아낀다" |
| 새 고객·매출 | "그 시간에 상담 2건을 더 받는다" |
| 데이터·사례 자산 축적 | "지점별 데이터를 쌓아 비교 리포트를 만들 수 있다" |
| 전문성 강화 | "분석에 쓸 시간이 생겨 판단이 더 정확해진다" |
| 이전에 불가능했던 상품 (최상) | "전 지점 실시간 현황이라는 새 상품을 팔 수 있다" |

`unlockedIfSolved`가 "그냥 편해진다" 수준에 머물면 그 고통은 지불로 이어지기 어렵다 — 이 판단도 기록에 남긴다.

---

## 4. "가장 비싼 문제" 선정법

`pains[]`가 2개 이상 모이면 순위를 매긴다. 절차:

1. **정량 비교** — `frequencyPerMonth × hoursPerOccurrence`(월 소요 시간)과 비용 필드(`directCost`·`errorCost`)를 나란히 놓는다. 정확한 곱셈 점수를 만들지 않는다 — 근거 없는 수치화는 금지(neuro-symbolic-rules.md).
2. **위험 가중** — `legalRisk`·`churnRisk`가 실재하는 고통은 시간이 적어도 순위를 올린다 (한 번의 사고가 월 30시간보다 비쌀 수 있다).
3. **기회 손실 가중** — `revenueLoss`·`unlockedIfSolved`의 층위가 높은 고통을 올린다.
4. **사용자에게 순위를 묻는다** — "이 중 내일 하나만 사라진다면 무엇을 고르겠습니까? 왜?" AI의 순위와 사용자의 순위가 다르면 그 차이를 파고든다(숨은 비용이나 숨은 가치가 드러난다).

최종 순위와 이유는 `severityNote`에 기록하고, 사용자가 확정한 1순위는 `decisions[]`(D-ID)에 남긴다.
1순위 고통은 이후 `reframe.observedProblem`과 `opportunities[]` 설계의 축이 된다.

---

## 5. 등록 예시

```json
{ "id": "P1", "eventIds": ["E1", "E2"],
  "description": "매주 금요일 여섯 지점 출결 파일 병합",
  "frequencyPerMonth": 4, "hoursPerOccurrence": 3,
  "directCost": "알바 주 1회 4만 원 (F5)", "errorCost": "병합 오류 시 학부모 항의 + 재발송 반나절 (E2)",
  "delayCost": "월말 정산이 매번 2~3일 밀림", "churnRisk": "항의 학부모 2명 퇴원 언급 (F7)",
  "revenueLoss": "", "qualityRisk": "", "legalRisk": "", "emotionalLoad": "금요일 오후가 매주 두렵다 (quote)",
  "alreadyPaid": "병합 매크로 외주 30만 원, 실패 (F6)",
  "unlockedIfSolved": "지점별 비교 데이터를 쌓아 원장 리포트 상품 가능",
  "severityNote": "월 12시간 + 이탈 위험 실재. 사용자 확정 1순위 (D2)" }
```

모든 서술 필드에 근거 ID(E/F)를 붙일 수 있어야 한다 — 붙일 수 없으면 그 값은 아직 가설이다.

---

## state 기록 요약

| 무엇을 | 어느 필드에 |
|--------|-------------|
| 고통 1건 (사건에 근거한) | `pains[]` (`id`:P, `eventIds`, `description`) |
| 빈도·시간 | `pains[].frequencyPerMonth`, `pains[].hoursPerOccurrence` |
| 비용 8종 | `directCost`, `errorCost`, `delayCost`, `churnRisk`, `revenueLoss`, `qualityRisk`, `legalRisk`, `emotionalLoad` |
| 이미 지불한 돈 | `pains[].alreadyPaid` + `ledger.facts` (지불 의사 선행 증거) |
| 해결 시 가능해지는 것 | `pains[].unlockedIfSolved` |
| 심각도 종합·순위 근거 | `pains[].severityNote` |
| 사용자가 확정한 1순위 고통 | `decisions[]` (D-ID) |
| 모르는 수치·미확인 항목 | `ledger.gaps` |
| 가짜 문제 판정 근거 (대안 존재 등) | `ledger.facts` / `severityNote` |
| 경제성 질문 (1개씩, 이유 포함) | `currentQuestion` (`text`, `why`, `gate:"economics"`) |
