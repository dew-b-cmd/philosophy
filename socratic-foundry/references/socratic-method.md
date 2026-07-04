# 소크라테스 논박 (Elenchus) — claims 검토 실행 지침

`elenchus` phase(Gate 8)에서 메인 Claude가 수행하는 논박 작업의 실행 지침이다.
목표는 사용자를 이기는 것이 아니라, 사업의 뼈대가 될 주장을 함께 두들겨 벼리는 것이다.
살아남은 주장(`survived`)만 reframe과 portfolio의 근거로 쓸 수 있다.

---

## 1. 논박 대상 주장 선정

state의 `ledger`·`pains`·`judgmentRules`·`stakeholders`·`session.initialStatement`에서
**핵심 주장 3~7개**를 추려 `claims[]`에 등록한다. 모든 발언을 논박하지 않는다 — 무너지면 아픈 것만 고른다.

우선순위 (높은 순):

1. **핵심 전제** — 이 주장이 무너지면 사업 구상 전체가 무너지는 것. 예: "소상공인은 이 문제에 돈을 낼 것이다."
2. **증거등급 D/E 주장** — `ledger.hypotheses`에만 있고 `ledger.facts`로 뒷받침되지 않는 것. 지불 의사·시장 규모·"누구나 필요" 류가 단골.
3. **사용자 확신이 강한 주장** — 답변 속도가 빠르고 단정적이며 "당연히", "무조건", "다들" 같은 표현이 붙은 것. 확신의 강도와 증거의 강도는 별개다.
4. **역할 혼동 주장** — 고객·구매자·사용자를 구분하지 않은 채 성립하는 주장 (`stakeholders.buyerIsSufferer`가 null이거나 false인데 "고객이 살 것"이라 말하는 경우).

등록 형식:

```json
{ "id": "CL1", "claim": "동네 학원장들은 출결 자동화에 월 5만 원을 낼 것이다",
  "status": "open", "checks": [] }
```

`claim`은 사용자의 말을 **검증 가능한 단문**으로 재서술한다. 재서술문은 사용자에게 보여주고 "이렇게 이해했는데 맞습니까?"를 먼저 확인한다 — 허수아비를 논박하지 않는다.

---

## 2. 5가지 검토 (checks)

주장 하나당 아래 5종을 순서대로 적용한다. 모든 주장에 5종 전부가 필수는 아니다 —
최소 3종(반드시 evidence 포함)을 적용하고, 통과가 뻔한 검토는 생략해도 된다.
각 검토는 `claims[].checks[]`에 1개 항목으로 기록한다.

### ① definition — 정의 요청

> "여기서 자동화는 정확히 무엇을 뜻합니까? 사람이 아예 안 보는 것입니까, 확인만 하는 것입니까?"

주장 속 추상어·다의어를 짚는다. 감지한 추상어는 `abstractions[]`에도 append 하고, 정의가 나오면 `resolved:true` + `definition`을 채운다 (상세는 maieutic-interview.md).

### ② consistency — 일관성 검토

> "앞에서는 맞춤형 서비스를 원한다 하셨지만, 방금은 대규모 확장도 원한다 하셨습니다. 어느 쪽이 우선입니까?"

`thread`와 `values`(특히 `antiGoals`, `customerDepth`)를 훑어 이 주장과 충돌하는 과거 발언을 찾는다. 충돌을 발견하면 §5의 모순 처리 절차를 따른다.

### ③ evidence — 근거 추궁 (생략 불가)

> "실제로 어떤 경험이 그 판단을 뒷받침합니까? 그 문제를 직접 말한 사람은 몇 명입니까?"

답이 실제 사건이면 `ledger.facts`에 F-ID로 append 하고 check의 `answer`에 그 ID를 언급한다. 답이 "느낌상", "아마도"면 verdict는 fail — 주장은 `ledger.hypotheses`로 강등하고 `gaps`에 미확인 질문을 남긴다.

### ④ alternative — 대안 탐색

> "소프트웨어를 만들지 않고도 이 문제를 해결할 수 있습니까? 엑셀 템플릿·외주·기존 도구 조합으로는 왜 안 됩니까?"

"이 해결 형태여야만 하는가"를 검사한다. 더 싼 대안이 성립하면 주장은 revised 대상이다.

### ⑤ consequence — 귀결 검토

> "이 방식을 선택하면 운영 비용과 고객 경험은 어떻게 달라집니까? 잘못 판단했을 때 누가 책임집니까?"

주장이 참일 때 따라오는 부담(운영·비용·책임·자동화 위험)을 추적한다. 자동화 관련 귀결은 `boundary[]` 기록의 입력이 된다.

---

## 3. checks 기록 방식

검토 1회 = check 1건. 사용자의 실제 답변을 요약해 `answer`에 담는다 (AI가 지어내지 않는다).

```json
{ "id": "CL1", "claim": "학원장들은 출결 자동화에 월 5만 원을 낼 것이다",
  "status": "revised",
  "checks": [
    { "kind": "definition", "question": "'자동화'는 학부모 알림까지 포함합니까?",
      "answer": "출결 기록만. 알림은 별개로 본다.", "verdict": "pass" },
    { "kind": "evidence", "question": "월 5만 원을 내겠다고 말한 학원장이 있습니까?",
      "answer": "직접 물어본 적은 없다. 불평은 3명에게 들었다(F4).", "verdict": "fail" },
    { "kind": "alternative", "question": "키오스크+구글시트 조합으로는 왜 안 됩니까?",
      "answer": "시트 병합이 매주 깨진다는 게 원래 불만이었다(E2).", "verdict": "pass" }
  ] }
```

---

## 4. verdict 판정 기준

| verdict | 기준 |
|---------|------|
| `pass` | 답변이 실제 사건·자료(`ledger.facts`의 F-ID)로 뒷받침되고, 다른 발언과 충돌 없음 |
| `fail` | 근거가 추정뿐이거나, 모순이 해소되지 않았거나, 더 싼 대안을 반박하지 못함 |
| `revised` | 검토 과정에서 사용자가 주장을 스스로 좁히거나 고침 — 고친 문장을 `answer`에 함께 기록 |

판정은 증거 기준으로만 한다. 사용자의 확신 강도·언짢음·시간 압박은 판정 근거가 아니다.

---

## 5. 주장 status 전이

| status | 조건 |
|--------|------|
| `open` | 등록 직후. checks가 비었거나 진행 중 |
| `survived` | evidence 포함 3종 이상 검토에서 fail 0건 |
| `revised` | fail이 나왔으나 사용자가 주장을 수정해 재검토에서 통과 — `claim` 필드를 수정문으로 갱신하고 checks에 이력 유지 |
| `withdrawn` | 사용자가 주장을 철회 — 삭제하지 않고 남긴다 (철회 자체가 인터뷰의 성과) |

fail 상태로 phase를 넘기지 않는다. fail이면 반드시 revise를 제안하거나 철회를 확인한다.
`withdrawn`·`revised` 주장에 근거했던 `ledger.inferences`가 있으면 `basis`를 재검토한다.

---

## 6. 모순 발견 시 — ledger.contradictions

consistency 검토(또는 인터뷰 중 우연히)에서 충돌을 발견하면 즉시 기록한다:

```json
{ "id": "C1", "a": "고객마다 맞춤 대응하고 싶다 (values.workStyle)",
  "b": "월 500곳 이상으로 확장하고 싶다 (CL3)",
  "status": "open", "resolution": "" }
```

그 다음 **양쪽을 나눌 기준을 묻는다** — "어떤 고객에게는 맞춤, 어떤 고객에게는 표준을 적용한다면 그 경계는 무엇입니까?" 해소되면 `status:"resolved"` + `resolution`을 채우고, 사용자가 한쪽을 택했다면 `decisions[]`에 D-ID로 기록한다. open인 모순을 남긴 채 reframe에 들어가면 verify-gate.py가 잡는다.

---

## 7. 과도한 확신 제거 요령

- **수치화 요구**: "확실하다"를 "10명 중 몇 명이 산다고 예상하십니까? 그 근거는?"으로 바꾼다.
- **반례 상상**: "이 주장이 틀렸다면, 가장 그럴듯한 이유는 무엇이겠습니까?" — 사용자가 반례를 하나도 못 대면 그 자체가 위험 신호(`vulnerabilities` 후보).
- **강등의 정상화**: fail이 나면 "주장이 죽은 게 아니라 가설(H-ID)로 자리를 옮긴 것"이라 말한다. 검증 실험(`experiments`)의 대상으로 넘긴다는 뜻이다.
- 한 주장에 fail이 3회 누적되면 논박을 멈추고 요약 후 사용자에게 revise/withdraw를 직접 선택하게 한다 — 심문이 되면 안 된다.

---

## 8. 톤 지침

- 논박은 공격이 아니라 **함께 벼리는 과정**이다. 시작할 때 한 번 명시한다: "지금부터 주장을 일부러 세게 두드립니다. 살아남은 주장만 계획서에 올릴 수 있기 때문입니다."
- 질문마다 `currentQuestion.why`에 왜 이 검토가 필요한지 쓴다. 이유 없는 추궁은 심문이다.
- 사용자의 주장이 fail해도 사람을 평가하지 않는다. "그 판단이 틀렸다"가 아니라 "그 판단을 뒷받침할 증거가 아직 없다"로 말한다.
- survived가 나오면 명확히 축하한다 — 살아남은 주장은 이후 모든 문서에서 자신 있게 인용된다.

---

## state 기록 요약

| 무엇을 | 어느 필드에 |
|--------|-------------|
| 논박 대상 주장 (검증 가능한 단문) | `claims[]` (`id`:CL, `claim`, `status:"open"`) |
| 검토 1회의 질문·답·판정 | `claims[].checks[]` (`kind`, `question`, `answer`, `verdict`) |
| 검토 결과에 따른 주장 상태 | `claims[].status` (open/survived/revised/withdrawn) |
| 검토 중 발견한 실제 사건·자료 | `ledger.facts` (F-ID, `source`) |
| 근거 없는 주장의 강등 | `ledger.hypotheses` (H-ID) + `ledger.gaps` |
| 발언 간 충돌 | `ledger.contradictions` (`a`, `b`, `status`, `resolution`) |
| 모순 해소 시 사용자의 선택 | `decisions[]` (D-ID, `basis`) |
| 주장 속 추상어 | `abstractions[]` (`term`, `resolved`, `definition`) |
| 귀결 검토에서 드러난 자동화 위험 | `boundary[]` 후보, `vulnerabilities[]` 후보 |
| 던지는 논박 질문 (한 번에 1개) | `currentQuestion` (`text`, `why`, `gate:"elenchus"`) |
