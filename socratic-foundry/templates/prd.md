<!--
  Socratic Foundry — PRD 템플릿 (outputs/prd.md)
  선택 기회(selected:true)의 form 이 제품형일 때 report 절차 3b 에서 생성한다.

  ★ 자기완결 원칙 (배포 전제): 이 스킬을 받은 사람에게는 다른 기획·빌드 스킬이 없다.
    이 PRD 는 외부 도구 없이 "이 파일 하나를 개발자나 AI 코딩 도구에 주면 개발이 시작되는" 최종 산출물이다.
    화면 명세·데이터 모델·개발 태스크를 전부 이 문서 안에서 완결한다.

  규칙 (SKILL.md §PRD 계약):
   - 기능마다 근거 ID(P/R/F/H) + 완료 기준(acceptance) 필수. 근거 없는 기능은 싣지 않거나 Won't.
   - 검증 안 된 전제는 [가설 H#] 표식 + 담당 실험 X# 명시. ethics 금지 5(기능 나열 PRD)를 '증거 연결'로 회피.
   - boundary 의 automation_forbidden 은 §8 비기능 요구사항의 '제품 가드'로 번역한다.
   - §9 개발 백로그의 각 Task 는 추가 맥락 없이 실행 가능한 문장으로 — AI 코딩 에이전트에 그대로 붙여넣을 수 있는 수준.
   - 외부 스킬 파이프라인 언급은 §12 '다음 단계' 의 옵션 경로에만 — 기본 경로는 "이 PRD 로 바로 개발".
-->

# {{PRODUCT_NAME}} — PRD (Product Requirements Document)

> 생성: {{DATE}} · 세션: {{SESSION_TITLE}} · 선택 기회: {{OPPORTUNITY_ID}} ({{FORM}})
> 이 PRD 의 모든 기능은 인터뷰 증거(F/P/R/H)로 추적된다. 검증 전 전제는 [가설]로 표시된다.

## 0. ⚠️ 개발 착수 조건 (먼저 읽을 것)

{{LAUNCH_GATES}}
<!-- 실험 X# 의 pass/fail 기준과 D#(중단·전환 기준)를 표로. "검증 전 착수 금지"가 원칙 —
     조건 충족 전에 개발을 시작하면 이 PRD 는 명세가 아니라 도박 계획서다. -->

## 1. 제품 개요

- **한 줄 정의**: {{ONE_LINER}}
- **배경 (승인된 문제 재정의)**: {{REFRAME_SUMMARY}} [결정 D#]
- **핵심 가치 3가지**: {{CORE_VALUES}} <!-- whyBuy 에서 — 시간 절약 이외 가치 -->

## 2. 목표와 성공 지표

{{GOALS_METRICS}}
<!-- values.successMinimum + 리텐션 등. 사용자가 말한 수치만 — 어림값은 어림값 표기 -->

## 3. 타겟 사용자

{{TARGET_USERS}}
<!-- stakeholders 기반. buyerIsSufferer 명시. 첫 고객 세그먼트와 접근 경로 현황 -->

## 4. 문제 정의와 해결 가설

{{PROBLEM_HYPOTHESES}}
<!-- P#(사건 근거 포함) + 해결 가설 H#(검증 상태 그대로) -->

## 5. 기능 요구사항 (MoSCoW)

<!-- 표: ID | 기능 | 설명 | 근거 | 완료 기준(acceptance) . Must/Should/Could/Won't 구분 -->
{{FEATURES_MOSCOW}}

## 6. 화면 명세와 핵심 플로우

{{SCREENS_FLOWS}}
<!-- 화면마다 목적·표시 데이터·입력·액션·연결 기능(FR)까지 — 별도 화면 명세 도구 없이
     이 표만으로 UI 개발에 착수할 수 있는 수준. + 핵심 사용자 플로우 2~3개 (목표 소요 시간 포함) -->

## 7. 데이터 모델 개요

{{DATA_MODEL}}
<!-- 엔티티·필드·관계 수준. 특정 스택 확정 금지 -->

## 8. 비기능 요구사항

{{NFR}}
<!-- 정확도(실험 기준 연동)·성능·개인정보·안전. boundary 의 automation_forbidden → 제품 가드로 번역 -->

## 9. 개발 백로그 (Phase별 Epic → Task)

<!-- 실제 개발 항목의 일목요연한 정리. 표: Task ID | 작업 | 영역(FE/BE/AI/Infra) | 근거 | 완료 기준.
     Phase 0 = 검증(개발 아님). 각 Task 는 추가 맥락 없이 실행 가능한 문장으로 —
     "이 표의 Phase 1 을 순서대로 구현해줘"라고 AI 코딩 도구에 붙여넣으면 되는 수준. -->
{{BACKLOG}}

## 10. Out of Scope (이번 버전에서 하지 않는 것)

{{OUT_OF_SCOPE}}
<!-- Won't + values.antiGoals + automation_forbidden 유래 항목. '왜 뺐는지' 한 줄씩 -->

## 11. 리스크와 완화

{{RISKS}}
<!-- V# 연결. 실험 결과에 따른 분기(D#) 재인용 -->

## 12. 다음 단계 — 이 PRD 를 들고 무엇을 하는가

{{NEXT_STEPS}}
<!-- 두 경로를 모두 제시한다 (report.html 의 다음 단계 안내와 동일 내용):
     경로 A (기본 — 별도 도구 불필요): 검증 게이트(§0) 통과 → 이 PRD 파일을 개발자 또는
       AI 코딩 도구(Claude Code 등)에 주고 "§9 Phase 1 백로그를 구현해줘"로 개발 시작.
     경로 B (옵션 — vibelabs 스킬팩 보유 시): /screen-spec(§6 입력) → /tasks-generator(§9 입력)
       → /auto-orchestrate 로 태스크 분해·자동 빌드.
     어느 경로든 §0 개발 착수 조건이 선행한다. -->

---

### 부록 — 근거 추적표

{{TRACE_TABLE}}
<!-- 기능 ID → 근거 ID → 원문 요약. 추적 안 되는 기능이 발견되면 그 기능을 지우거나 Won't 로 -->
