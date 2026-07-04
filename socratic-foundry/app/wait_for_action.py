#!/usr/bin/env python3
"""
Socratic Foundry — 백그라운드 대기 폴러

state.json 의 pendingAction 이 채워질 때까지 폴링하다가, 채워지면 그 액션을 stdout 에
한 줄(JSON)로 출력하고 종료한다. 이 프로세스가 종료되면 메인 Claude(오케스트레이터)가
재호출되어 액션을 처리한다(계약: references/session-protocol.md).

사용법:  python3 wait_for_action.py <session_dir> [timeout_sec]
출력:
  ACTION {json}     ← 처리할 액션 발생
  TIMEOUT           ← timeout 동안 무응답 (메인은 재기동하거나 멈춤)
"""

import sys, os, json, time

SESSION_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
TIMEOUT = float(sys.argv[2]) if len(sys.argv) > 2 else 1800.0
STATE_PATH = os.path.join(SESSION_DIR, "state.json")
INTERVAL = 1.0

start = time.time()
while True:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            s = json.load(f)
        act = s.get("pendingAction")
        if act:
            print("ACTION " + json.dumps(act, ensure_ascii=False), flush=True)
            sys.exit(0)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass  # 서버가 atomic write 중일 수 있음 — 다음 폴링에서 재시도

    if time.time() - start > TIMEOUT:
        print("TIMEOUT", flush=True)
        sys.exit(0)
    time.sleep(INTERVAL)
