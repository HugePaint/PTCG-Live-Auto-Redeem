import time
from pathlib import Path

import pyautogui
import pyperclip
import pygetwindow as gw

from config import (
    AFTER_CLICK_WAIT,
    AFTER_PASTE_WAIT,
    AFTER_REDEEM_WAIT,
    AFTER_SUBMIT_WAIT,
    CONFIDENCE,
    DUPLICATE_IMG,
    ERROR_IMG,
    INPUT_BOX_IMG,
    RECAPTCHA_IMG,
    REDEEMED_IMG,
    REGION_PADDING_BOTTOM,
    REGION_PADDING_LEFT,
    REGION_PADDING_RIGHT,
    REGION_PADDING_TOP,
    SEARCH_TIMEOUT,
    STATUS_POLL_INTERVAL,
    STATUS_TIMEOUT,
    SUBMIT_BUTTON_IMG,
    SUCCESS_IMG,
    REDEEM_BUTTON_IMG,
)


def get_browser_window(keyword: str):
    all_titles = gw.getAllTitles()
    matched = []

    for title in all_titles:
        if title and keyword.lower() in title.lower():
            matched.extend(gw.getWindowsWithTitle(title))

    unique = []
    seen = set()
    for w in matched:
        key = (w.title, w.left, w.top, w.width, w.height)
        if key not in seen:
            seen.add(key)
            unique.append(w)

    if not unique:
        raise RuntimeError(
            f"未找到标题包含关键字 [{keyword}] 的窗口。\n"
            f"可尝试改成更宽松的值，比如 Chrome、redeem.tcg.pokemon.com 等。"
        )

    return max(unique, key=lambda w: w.width * w.height)


def activate_window(window) -> None:
    try:
        if window.isMinimized:
            window.restore()
            time.sleep(0.8)
        window.activate()
        time.sleep(1.0)
    except Exception as e:
        print(f"窗口激活失败，继续尝试使用当前窗口: {e}")


def get_search_region(window):
    x = max(window.left + REGION_PADDING_LEFT, 0)
    y = max(window.top + REGION_PADDING_TOP, 0)
    w = max(window.width - REGION_PADDING_LEFT - REGION_PADDING_RIGHT, 1)
    h = max(window.height - REGION_PADDING_TOP - REGION_PADDING_BOTTOM, 1)
    return (x, y, w, h)


def wait_and_locate_center(
    image_path: Path,
    desc: str,
    region,
    timeout: float = SEARCH_TIMEOUT,
    confidence: float = CONFIDENCE,
):
    if not image_path.exists():
        raise FileNotFoundError(f"模板图片不存在: {image_path}")

    start = time.time()
    while time.time() - start < timeout:
        pos = pyautogui.locateCenterOnScreen(
            str(image_path),
            confidence=confidence,
            grayscale=False,
            region=region,
        )
        if pos is not None:
            return pos
        time.sleep(0.3)

    raise TimeoutError(f"在区域 {region} 内，{timeout} 秒内未找到: {desc}")


def locate_on_screen_optional(image_path: Path, region, confidence: float = CONFIDENCE):
    if not image_path.exists():
        return None

    return pyautogui.locateOnScreen(
        str(image_path),
        confidence=confidence,
        grayscale=False,
        region=region,
    )


def click_image(image_path: Path, desc: str, region):
    pos = wait_and_locate_center(image_path, desc, region=region)
    pyautogui.click(pos.x, pos.y)
    return pos


def paste_text(text: str) -> None:
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")


def clear_input_box(region) -> None:
    click_image(INPUT_BOX_IMG, "输入框", region)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    time.sleep(0.1)


def detect_redeem_status(region) -> tuple[str, str]:
    """
    status: SUCCESS / RECAPTCHA / REDEEMED / DUPLICATE / ERROR
    """
    start = time.time()

    while time.time() - start < STATUS_TIMEOUT:
        if locate_on_screen_optional(SUCCESS_IMG, region):
            return "SUCCESS", "匹配到 success.png"

        if locate_on_screen_optional(RECAPTCHA_IMG, region):
            return "RECAPTCHA", "匹配到 recaptcha.png"

        if locate_on_screen_optional(REDEEMED_IMG, region):
            return "REDEEMED", "匹配到 redeemed.png"

        if locate_on_screen_optional(DUPLICATE_IMG, region):
            return "DUPLICATE", "匹配到 duplicate.png"

        if locate_on_screen_optional(ERROR_IMG, region):
            return "ERROR", "匹配到 error.png"

        time.sleep(STATUS_POLL_INTERVAL)

    return "ERROR", f"{STATUS_TIMEOUT} 秒内未识别到状态提示"


def process_code(code: str, index: int, total: int, region) -> tuple[str, str]:
    clear_input_box(region)
    time.sleep(AFTER_CLICK_WAIT)

    paste_text(code)
    time.sleep(AFTER_PASTE_WAIT)

    click_image(SUBMIT_BUTTON_IMG, "SUBMIT CODE", region)
    time.sleep(AFTER_SUBMIT_WAIT)

    click_image(REDEEM_BUTTON_IMG, "REDEEM", region)
    time.sleep(AFTER_REDEEM_WAIT)

    status, detail = detect_redeem_status(region)

    if status == "RECAPTCHA":
        pyautogui.press("f5")
        time.sleep(3.0)

    return status, detail
