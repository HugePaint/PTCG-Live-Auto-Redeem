from datetime import datetime
from pathlib import Path

import pyautogui

from config import RESULTS_FILE, FAILED_CODES_FILE, DEBUG_DIR, TEMPLATE_BACKUP_DIR


def ensure_dirs() -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def append_result(code: str, status: str, detail: str = "") -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        line = f"{now} | {code} | {status} | {detail}\n"
    else:
        line = f"{now} | {code} | {status}\n"

    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def append_failed_code(code: str) -> bool:
    """
    将失败 code 写入 failed_codes.txt
    返回值:
        True  -> 本次新写入
        False -> 文件里已存在，未重复写入
    """
    code = code.strip()
    if not code:
        return False

    existing = set()
    if FAILED_CODES_FILE.exists():
        existing = {
            line.strip()
            for line in FAILED_CODES_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    if code in existing:
        return False

    with FAILED_CODES_FILE.open("a", encoding="utf-8") as f:
        f.write(code + "\n")

    return True


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
