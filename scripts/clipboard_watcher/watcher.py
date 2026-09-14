"""클립보드 감시 진입점.

Windows에서 실행 예정 (개발은 Linux) - 경로는 pathlib로 처리해서 OS 차이를 피함.
"""

import os
import time
from datetime import datetime

import pyperclip
from dotenv import load_dotenv

from parser import parse_clipboard
from savers import save

load_dotenv()
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "3"))


def log(action: str, path, lines: int) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {action} {path} lines={lines}")


def watch() -> None:
    print(f"클립보드 감시 시작 (간격 {POLL_INTERVAL}초, 저장 폴더: {OUTPUT_DIR})")
    last = ""
    while True:
        try:
            current = pyperclip.paste()
        except Exception as e:
            print(f"클립보드 읽기 실패: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        if current != last:
            last = current
            result = parse_clipboard(current)
            if result:
                meta, payload = result
                try:
                    saved = save(meta, payload, OUTPUT_DIR)
                    if saved:
                        action, path, lines = saved
                        log(action, path, lines)
                except Exception as e:
                    print(f"저장 실패: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        watch()
    except KeyboardInterrupt:
        print("종료합니다.")
