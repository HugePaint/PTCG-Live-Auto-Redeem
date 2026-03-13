import time
from datetime import datetime
from pathlib import Path

import pyautogui
import pyperclip
import pygetwindow as gw

# =========================
# 基本配置
# =========================
CODES_FILE = Path("codes.txt")
RESULTS_FILE = Path("results.txt")
TEMPLATE_DIR = Path("templates")
DEBUG_DIR = Path("debug_screenshots")

INPUT_BOX_IMG = TEMPLATE_DIR / "input_box.png"
SUBMIT_BUTTON_IMG = TEMPLATE_DIR / "submit_button.png"
REDEEM_BUTTON_IMG = TEMPLATE_DIR / "redeem_button.png"

SUCCESS_IMG = TEMPLATE_DIR / "success.png"
RECAPTCHA_IMG = TEMPLATE_DIR / "recaptcha.png"
REDEEMED_IMG = TEMPLATE_DIR / "redeemed.png"
DUPLICATE_IMG = TEMPLATE_DIR / "duplicate.png"
ERROR_IMG = TEMPLATE_DIR / "error.png"

WINDOW_TITLE_KEYWORD = "Redeem Pokémon TCG Live Codes"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

START_DELAY = 3.0
CONFIDENCE = 0.75
SEARCH_TIMEOUT = 8.0
STATUS_TIMEOUT = 10.0
STATUS_POLL_INTERVAL = 0.4

AFTER_CLICK_WAIT = 0.4
AFTER_PASTE_WAIT = 0.3
AFTER_SUBMIT_WAIT = 1.2
AFTER_REDEEM_WAIT = 1.5

REGION_PADDING_LEFT = 10
REGION_PADDING_TOP = 120
REGION_PADDING_RIGHT = 10
REGION_PADDING_BOTTOM = 20


def ensure_dirs():
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def get_next_code(file_path: Path) -> tuple[str, list[str]] | None:
    if not file_path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    raw_lines = file_path.read_text(encoding="utf-8").splitlines()
    codes = [line.strip() for line in raw_lines if line.strip()]

    if not codes:
        return None

    current_code = codes[0]
    remaining_codes = codes[1:]
    return current_code, remaining_codes


def write_remaining_codes(file_path: Path, remaining_codes: list[str]) -> None:
    content = "\n".join(remaining_codes)
    if content:
        content += "\n"
    file_path.write_text(content, encoding="utf-8")


def append_result(code: str, status: str, detail: str = "") -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if detail:
        line = f"{now} | {code} | {status} | {detail}\n"
    else:
        line = f"{now} | {code} | {status}\n"

    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

    print("日志:", line.strip())


def get_pending_code_count(file_path: Path) -> int:
    if not file_path.exists():
        return 0
    lines = file_path.read_text(encoding="utf-8").splitlines()
    return sum(1 for line in lines if line.strip())


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
            f"你可以把 WINDOW_TITLE_KEYWORD 改成更宽松的值，比如 Chrome、redeem.tcg.pokemon.com 等。"
        )

    return max(unique, key=lambda w: w.width * w.height)


def activate_window(window):
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

    region = (x, y, w, h)
    print(f"搜索区域 region = {region}")
    return region


def wait_and_locate_center(
    image_path: Path,
    desc: str,
    region,
    timeout: float = SEARCH_TIMEOUT,
    confidence: float = CONFIDENCE
):
    if not image_path.exists():
        raise FileNotFoundError(f"模板图片不存在: {image_path}")

    start = time.time()
    while time.time() - start < timeout:
        pos = pyautogui.locateCenterOnScreen(
            str(image_path),
            confidence=confidence,
            grayscale=False,
            region=region
        )
        if pos is not None:
            print(f"找到 {desc}: ({pos.x}, {pos.y})")
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
        region=region
    )


def click_image(image_path: Path, desc: str, region):
    pos = wait_and_locate_center(image_path, desc, region=region)
    pyautogui.click(pos.x, pos.y)
    print(f"点击 {desc}: ({pos.x}, {pos.y})")
    return pos


def paste_text(text: str):
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")


def clear_input_box(region):
    click_image(INPUT_BOX_IMG, "输入框", region)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    time.sleep(0.1)


def save_debug_screenshot(code: str, tag: str, region=None) -> Path:
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_code = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in code)[:40]
    path = DEBUG_DIR / f"{now_str}_{safe_code}_{tag}.png"

    if region is None:
        screenshot = pyautogui.screenshot()
    else:
        screenshot = pyautogui.screenshot(region=region)

    screenshot.save(path)
    print(f"已保存调试截图: {path}")
    return path


def detect_redeem_status(region) -> tuple[str, str]:
    """
    在提交/兑换后轮询页面提示图，返回:
    (status, detail)

    status: SUCCESS / RECAPTCHA / REDEEMED / DUPLICATE / ERROR / UNKNOWN
    """
    start = time.time()

    while time.time() - start < STATUS_TIMEOUT:
        # 按优先级检查
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

    return "ERROR", f"{STATUS_TIMEOUT} 秒内未识别到 success/duplicate/error 提示"


def process_code(code: str, index: int, total: int, region) -> tuple[str, str]:
    print(f"\n[{index}/{total}] 处理 code: {code}")

    # 1. 点击输入框并清空
    clear_input_box(region)
    time.sleep(AFTER_CLICK_WAIT)

    # 2. 粘贴 code
    paste_text(code)
    time.sleep(AFTER_PASTE_WAIT)

    # 3. 点击 SUBMIT CODE
    click_image(SUBMIT_BUTTON_IMG, "SUBMIT CODE", region)
    time.sleep(AFTER_SUBMIT_WAIT)

    # 4. 点击 REDEEM
    click_image(REDEEM_BUTTON_IMG, "REDEEM", region)
    time.sleep(AFTER_REDEEM_WAIT)

    # 5. 检测状态
    status, detail = detect_redeem_status(region)
    print(f"识别结果: {status} | {detail}")

    # 6. RECAPTCHA 时刷新
    if status == "RECAPTCHA":
        print("检测到 RECAPTCHA，尝试刷新页面")
        pyautogui.press("f5")
        time.sleep(3.0)

    return status, detail


def main():
    ensure_dirs()

    pending_count = get_pending_code_count(CODES_FILE)
    print(f"读取到 {pending_count} 个待处理 code")
    print(f"{START_DELAY} 秒后开始")
    print("将鼠标移动到左上角可紧急停止")
    time.sleep(START_DELAY)

    window = get_browser_window(WINDOW_TITLE_KEYWORD)
    print(f"找到窗口: {window.title}")
    print(f"窗口位置: left={window.left}, top={window.top}, width={window.width}, height={window.height}")

    activate_window(window)
    region = get_search_region(window)

    processed = 0

    while True:
        item = get_next_code(CODES_FILE)
        if item is None:
            print("codes.txt 已处理完，全部完成")
            break

        code, remaining_codes = item
        total_now = processed + len(remaining_codes) + 1

        try:
            status, detail = process_code(code, processed + 1, total_now, region)

            # 为了排查识别问题，非 SUCCESS 时自动截图
            if status != "SUCCESS":
                save_debug_screenshot(code, status.lower(), region)

        except pyautogui.FailSafeException:
            append_result(code, "STOPPED", "触发 PyAutoGUI failsafe，脚本终止")
            write_remaining_codes(CODES_FILE, remaining_codes)
            raise

        except Exception as e:
            status = "ERROR"
            detail = f"脚本异常: {e}"
            save_debug_screenshot(code, "exception", region)

        append_result(code, status, detail)
        write_remaining_codes(CODES_FILE, remaining_codes)

        processed += 1

    print("results.txt 已更新")


if __name__ == "__main__":
    main()
