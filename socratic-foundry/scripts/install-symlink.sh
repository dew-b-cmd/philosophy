#!/usr/bin/env bash
# Socratic Foundry — 전역 스킬 심링크 등록
#
# 이 스킬 폴더를 ~/.claude/skills/socratic-foundry 로 심링크해 전역에서 호출 가능하게 한다.
# 저장소 관행: 스킬별 개별 심링크, 절대경로. 등록 후 Claude Code 세션 재시작 시 자동 발견.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_HOME="${HOME}/.claude/skills"
LINK="${SKILLS_HOME}/socratic-foundry"

mkdir -p "${SKILLS_HOME}"

if [ -L "${LINK}" ]; then
  echo "이미 심링크 존재: ${LINK} -> $(readlink "${LINK}")"
  echo "재설정하려면 먼저 'rm ${LINK}' 후 다시 실행하세요."
  exit 0
elif [ -e "${LINK}" ]; then
  echo "오류: ${LINK} 가 이미 실제 파일/폴더로 존재합니다. 충돌을 피하려면 수동 확인이 필요합니다." >&2
  exit 1
fi

ln -s "${SKILL_DIR}" "${LINK}"
echo "심링크 생성 완료:"
ls -la "${LINK}"
echo
echo "→ Claude Code 세션을 재시작하면 'socratic-foundry' 스킬이 인식됩니다."
