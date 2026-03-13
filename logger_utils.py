from datetime import datetime
from pathlib import Path

import pyautogui

from config import RESULTS_FILE, DEBUG_DIR


def ensure_dirs() -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def append_result(code: str, status: str, detail: str = "") -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        line = f"{now} | {code} | {status} | {detail}\n"
    else:
        line = f"{now} | {code} | {status}\n"

    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def save_debug_screenshot(code: str, tag: str, region=None) -> Path:
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_code = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in code)[:40]
    path = DEBUG_DIR / f"{now_str}_{safe_code}_{tag}.png"

    if region is None:
        screenshot = pyautogui.screenshot()
    else:
        screenshot = pyautogui.screenshot(region=region)

    screenshot.save(path)
    return path
