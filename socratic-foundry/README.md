# Socratic Foundry — 소크라틱 파운드리

> 무엇을 만들고 싶은지 묻는 데서 멈추지 않습니다.
> 당신이 **무엇을 만들어야 하는지** 함께 찾아냅니다.

사용자의 경험과 암묵지에서 문제를 발굴하고 사업 기회로 주조하는 **소크라테스식 AI 기획 인터뷰
시스템**입니다. Claude Code 스킬로 실행되며, 인터뷰는 로컬 브라우저 HTML 화면에서 진행됩니다.

- 아이디어를 참이라고 전제하지 않습니다 — 전제를 먼저 의심합니다
- 진술보다 사건, 관심보다 전문성, 효율보다 효과를 신뢰합니다
- 모든 결론은 [사실]/[추론]/[가설]/[제안]/[결정] 표식과 근거 ID 로 추적됩니다
- 기획서가 아니라 **7~14일 안에 실행 가능한 검증 실험**으로 끝납니다

## 설치

```bash
bash scripts/install-symlink.sh   # ~/.claude/skills/socratic-foundry 심링크 등록
```

Claude Code 세션을 재시작하면 인식됩니다. 의존성 없음 — Python 3 표준 라이브러리만 사용합니다.

## 사용

Claude Code 에서:

```
/socratic-foundry
```

또는 자연어로 — "내 경험으로 뭘 만들지 모르겠어", "이 아이디어 논박해줘", "내 지식 상품화하고 싶어".

브라우저가 열리면 **인터뷰 계약**(Gate 0)에서 모드를 고르고 최초 진술을 적습니다.
이후 모든 진행은 브라우저에서: 답하고 → 버튼을 누르면 → Claude 가 이어받아 다음 화면을 만듭니다.

### 5개 모드

| 모드 | 시간 | 결과 |
|------|------|------|
| Quick Scan | 10~15분 | 핵심 문제·자산 후보, 추천 형태 2~3개, 추가 탐색 질문 |
| Standard Discovery | 30~45분 | 문제 구조, 도메인 지도, 고객·구매자, 기회 포트폴리오, 7일 실험 |
| Deep Mining | 60~90분+ | 경력 전반 암묵지, 지식그래프, 논박, 취약점 감사, 30·90일 계획 |
| Idea Challenge | 30~60분 | 기존 아이디어를 논박·재정의 |
| Domain Productization | 40~60분 | 지식·컨설팅·강의를 상품으로 변환 |

### 인터뷰 게이트 (deep 모드 기준)

계약 → 가치와 방향 → 문제 장면 → 고통의 경제성 → 암묵지 채굴 → 지식그래프 →
역량과 자원 → 고객과 구매자 → 소크라테스 논박 → 문제 재정의(사용자 승인) →
취약점 감사 → 기회 포트폴리오 → 검증 실험 → 최종 산출물

게이트 통과는 Claude 의 "느낌"이 아니라 `scripts/verify-gate.py`(심볼릭 검증기)가 판정합니다.

## 산출물

세션 폴더(`socratic-foundry-sessions/{날짜}-{제목}/`) 의 `outputs/` 에:

```
one-page-brief.md          # One-page Opportunity Thesis (15항목 + 최종 문장 6줄)
full-planning-report.md    # 상세 기획서 (모든 주장에 표식 + 근거 ID)
report.html                # 종합 HTML (그래프·print.css 내장 — 브라우저 인쇄로 PDF)
evidence-ledger.md         # 증거 원장 (사실/추론/가설/모순/공백)
painpoint-map.md           # 고통 지도
opportunity-portfolio.md   # 기회 포트폴리오 (3축 평가)
human-ai-boundary.md       # 인간-AI 업무 경계 (자동화 금지 영역 포함)
validation-plan.md         # 검증 계획
interview-transcript.md    # 인터뷰 전문
```

모든 데이터는 로컬에만 저장됩니다. 세션 폴더 삭제 = 완전 삭제.

## 구조

```
socratic-foundry/
├── SKILL.md                     # 메인 플레이북 (이벤트 루프·절대 규칙)
├── references/                  # 방법론 (session-protocol.md 가 스키마 SSOT)
├── agents/                      # 10개 역할 카드 (인터뷰어·지도사·논박관·설계자·비판자·코치…)
├── app/
│   ├── server.py                # 로컬 HTML 인터뷰 서버 (stdlib 전용, 렌더+이벤트 캡처만)
│   └── wait_for_action.py       # 대기 폴러 (버튼 → Claude 재호출)
├── schemas/                     # state·그래프·증거·기회·보고서 JSON Schema
├── rules/                       # 게이트·모순·증거·안전 규칙 (심볼릭 층 데이터)
├── scripts/
│   ├── verify-gate.py           # 하드 게이트 검증기
│   └── install-symlink.sh
└── templates/                   # one-page-brief.md · full-report.md · report.html
```

### 아키텍처 — 뉴로심볼릭 분리

| 층 | 담당 | 책임 |
|----|------|------|
| 신경망 | 메인 Claude | 질문 생성, 암묵지 분해, 논박, 기회 설계, 문서 작성 |
| 심볼릭 | server.py / verify-gate.py / rules·schemas | 화면 렌더, 게이트 판정, 사실·추론 분리 강제, 모순·증거 추적 |

서버는 절대 사고하지 않고, Claude 는 절대 HTML 을 직접 그리지 않습니다.
둘은 세션 폴더의 `state.json` 하나로만 대화합니다 (단일 진실 소스).

### 기획서(v2.0) 대비 구현 노트

- §20 기술 아키텍처의 React/Fastify/SQLite/Playwright 스택은 **로드맵**입니다. 현재 구현은
  이 저장소 스킬들의 검증된 패턴(stdlib 서버 + state.json 라운드트립)으로 §23 MVP 범위를
  전부 충족합니다 — 로컬 HTML 인터뷰, 적응형 질문, 상태 저장·재개, 지식그래프, 모순 탐지,
  고객·구매자 분리, 기회 3개+, 검증 실험, MD·HTML·PDF(브라우저 인쇄) 출력.
- 세션 저장은 SQLite 대신 폴더별 `state.json` (버전 필드·원자적 쓰기). FTS 검색은 미포함.
- PDF 는 Playwright 대신 `report.html` 의 print.css + 브라우저 인쇄(기획서의 예비 경로).

## 금지 규칙 (일부)

"누구나 쓰는 혁신적 플랫폼" 류 산출물 · 근거 없는 시장 규모 · 모든 문제의 SaaS 화 ·
말하지 않은 전문성 과장 · AI 추론을 사실처럼 기록 · 검증 없이 개발부터 시작하는 계획 ·
개인적 상처의 마케팅 소재화. 전체 목록: `rules/safety-rules.json`.
