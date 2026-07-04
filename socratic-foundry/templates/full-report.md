<!--
  Socratic Foundry — 상세 기획서 템플릿 (full-planning-report.md)
  {{…}} 를 state.json 내용으로 치환한다.
  규칙 (schemas/report.schema.json · references/neuro-symbolic-rules.md):
   - 모든 주요 주장에 [사실]/[추론]/[가설]/[제안]/[결정] 표식 + 근거 ID 병기
   - AI 추론을 사용자 사실처럼 쓰지 않는다. 근거 없는 시장 규모·매출 전망 금지
   - 게이트 FAIL 상태로 이 문서를 만들지 않는다 (verify-gate.py --all 선행)
-->

# {{SESSION_TITLE}} — 기획 보고서

> 생성 {{DATE}} · 모드 {{MODE}} · Socratic Foundry
> 하드 게이트: {{GATE_SUMMARY}}

## 0. 요약 (최종 문장)

{{FINAL_SIX_LINES}}
<!-- one-page-brief 의 최종 문장 6줄 -->

---

## 1. 인터뷰 계약 (Gate 0)

- **목적**: {{PURPOSE}} [결정 D1]
- **유형**: {{GOAL_TYPE}} · **깊이 합의**: {{DEPTH_CONSENT}} · **금지 영역**: {{OFF_LIMITS}}
- **인터뷰 후 내릴 결정**: {{DESIRED_DECISION}}
- **최초 진술**: "{{INITIAL_STATEMENT}}"

## 2. 가치와 방향 (Gate 1)

{{VALUES_SECTION}}
<!-- workStyle / priorities(순서) / antiGoals / customerDepth / teamPreference / successMinimum. 전부 [결정] -->

## 3. 문제의 실제 장면 (Gate 2)

{{EVENTS_SECTION}}
<!-- 사건별: E# / 언제 / 무엇을 하다가 / 관련 인물·도구 / 막힌 곳 / 걸린 시간 / 임시방편 / 포기한 것 / 인용. 전부 [사실] -->

## 4. 고통의 경제성 (Gate 3)

{{PAINS_TABLE}}
<!-- P# | 문제 | 월 빈도 | 1회 시간 | 손실(비용/오류/지연/이탈/매출/품질/법적/감정) | 이미 쓴 돈 | 해결 시 얻는 것 -->

**가장 비싼 문제**: {{MOST_EXPENSIVE_PROBLEM}} [추론 — 근거: {{MEP_BASIS}}]

## 5. 암묵지와 판단 규칙 (Gate 4)

{{JUDGMENT_RULES_SECTION}}
<!-- R#: 규칙 / 신호 / 실제 사례 / 예외 / 초보자 실수 / confidence(경험·재능·미검증) -->

### 비대칭 자산

{{ASSETS_SECTION}}
<!-- A#: 종류 / 설명 / 근거 / 복제 난이도 -->

## 6. 도메인 지식그래프 (Gate 5)

{{GRAPH_SECTION}}
<!-- 트리 텍스트 렌더 + 노드 status 표기. confirmed 만 결론에 사용. proposed/needs_evidence 는 '미확인'으로 명시 -->

## 7. 역량과 자원 (Gate 6)

{{CAPABILITIES_SECTION}}
<!-- 10 영역 서술 평가. 등급 딱지 금지. 예: "도메인 전문성은 매우 높지만 판매 경험이 부족 → 유료 진단 서비스 우선 경로" -->

## 8. 고객과 이해관계자 (Gate 7)

{{STAKEHOLDERS_SECTION}}
<!-- 8역할 분리 표 + buyerIsSufferer + statusQuoWinner + accessPath + firstCustomer -->

## 9. 소크라테스 논박 (Gate 8)

{{ELENCHUS_SECTION}}
<!-- CL#: 주장 / 5종 검토(정의·일관성·근거·대안·귀결) 문답 / verdict / 최종 status. 철회·수정된 주장도 기록 -->

### 모순 기록

{{CONTRADICTIONS_SECTION}}
<!-- C#: a ↔ b / 해소(resolution) 또는 '미해소 긴장' 명시 -->

## 10. 문제 재정의 (Gate 9)

| 층 | 내용 |
|---|---|
| 최초 진술 | {{INITIAL_STATEMENT}} |
| 관찰된 문제 | {{OBSERVED_PROBLEM}} |
| 더 깊은 문제 | {{DEEPER_PROBLEM}} |
| 사업 기회 | {{OPPORTUNITY_STATEMENT}} |

사용자 승인: {{REFRAME_VERDICT}} [결정 {{REFRAME_DECISION_ID}}]

## 11. 취약점 감사 (Gate 10)

{{VULNERABILITIES_SECTION}}
<!-- V#: 범주 / 설명 / 심각도 / 근거 / 대응 / isRiskiestAssumption 표시 -->

## 12. 기회 포트폴리오 (Gate 11)

{{OPPORTUNITIES_SECTION}}
<!-- O# 별 카드: horizon / form / pitch / 고객·구매자 / 잠재가치 n/5 (why) / 적합성 n/5 (why) /
     증거등급 X (why) / whyBuy / assetBuilt / whyYou / biggestRisk / 선택 여부.
     Critic 반박에서 수정·강등된 이력이 있으면 명시 -->

**선택된 기회**: {{SELECTED_OPPORTUNITIES}} [결정 {{SELECTION_DECISION_ID}}]

## 13. 인간과 AI 의 업무 경계

{{BOUNDARY_TABLE}}
<!-- 업무 | 모드(6종) | 이유. automation_forbidden 최소 1개 -->

## 14. 검증 계획

{{EXPERIMENTS_SECTION}}
<!-- X#: 제목 / 겨냥하는 가장 위험한 가설 / 행동 / 대상 / 기간(≤14일) / 지표 / 통과·실패·중단 기준 / 비용 -->

## 15. 실행 계획

- **7일 행동**: {{SEVEN_DAY_ACTION}}
- **30일**: {{THIRTY_DAY_PLAN}} <!-- deep 모드만. 아니면 "다음 세션에서 설계" -->
- **90일**: {{NINETY_DAY_PLAN}}
- **중단·전환 기준**: {{STOP_OR_PIVOT}}

---

## 부록 A. 증거 원장 요약

{{LEDGER_SUMMARY}}
<!-- 사실 F(개수+목록) / 추론 I(basis 포함) / 가설 H(testedBy) / 모순 C / 공백 gaps. 상세는 evidence-ledger.md -->

## 부록 B. 게이트 검사 결과

```
{{GATE_REPORT}}
```

## 부록 C. 미해소 긴장·한계

{{OPEN_TENSIONS}}
<!-- open contradiction, 증거 D/E 항목, 생략된 게이트(모드 정책). 숨기지 않는다 -->
