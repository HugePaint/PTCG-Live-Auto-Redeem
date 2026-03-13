import time
from pathlib import Path

import pyautogui
import pyperclip

# =========================
# 基本配置
# =========================
CODES_FILE = Path("codes.txt")
TEMPLATE_DIR = Path("templates")

INPUT_BOX_IMG = TEMPLATE_DIR / "input_box.png"
SUBMIT_BUTTON_IMG = TEMPLATE_DIR / "submit_button.png"
REDEEM_BUTTON_IMG = TEMPLATE_DIR / "redeem_button.png"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.25

START_DELAY = 5.0
CONFIDENCE = 0.8          # 识别置信度，0.7~0.9 常用
SEARCH_TIMEOUT = 8.0      # 每次查找控件的超时时间

AFTER_CLICK_WAIT = 0.4
AFTER_PASTE_WAIT = 0.3
AFTER_SUBMIT_WAIT = 1.5
AFTER_REDEEM_WAIT = 2.0


def read_codes(file_path: Path) -> list[str]:
    if not file_path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    lines = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines()]
    codes = [line for line in lines if line]
    if not codes:
        raise ValueError("codes.txt 里没有可用内容")
    return codes


def wait_and_locate_center(image_path: Path, desc: str, timeout: float = SEARCH_TIMEOUT, confidence: float = CONFIDENCE):
    """
    在屏幕上等待并查找模板图片，返回中心坐标 (x, y)
    """
    if not image_path.exists():
        raise FileNotFoundError(f"模板图片不存在: {image_path}")

    start = time.time()
    while time.time() - start < timeout:
        location = pyautogui.locateCenterOnScreen(
            str(image_path),
            confidence=confidence,
            grayscale=False
        )
        if location is not None:
            print(f"找到 {desc}: {location}")
            return location
        time.sleep(0.3)

    raise TimeoutError(f"在 {timeout} 秒内未找到: {desc}")


def click_image(image_path: Path, desc: str):
    pos = wait_and_locate_center(image_path, desc)
    pyautogui.click(pos.x, pos.y)
    print(f"点击 {desc}: ({pos.x}, {pos.y})")
    return pos


def paste_text(text: str):
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")


def process_code(code: str, index: int, total: int):
    print(f"\n[{index}/{total}] 处理 code: {code}")

    # 1. 点击输入框
    click_image(INPUT_BOX_IMG, "输入框")
    time.sleep(AFTER_CLICK_WAIT)

    # 2. 粘贴 code
    paste_text(code)
    time.sleep(AFTER_PASTE_WAIT)

    # 3. 点击 SUBMIT CODE
    click_image(SUBMIT_BUTTON_IMG, "SUBMIT CODE")
    time.sleep(AFTER_SUBMIT_WAIT)

    # 4. 点击 REDEEM
    click_image(REDEEM_BUTTON_IMG, "REDEEM")
    time.sleep(AFTER_REDEEM_WAIT)


def main():
    codes = read_codes(CODES_FILE)

    print(f"读取到 {len(codes)} 个 code")
    print(f"{START_DELAY} 秒后开始，请把浏览器页面切到前台并保持可见")
    print("将鼠标移到屏幕左上角可紧急停止")
    time.sleep(START_DELAY)

    for i, code in enumerate(codes, start=1):
        process_code(code, i, len(codes))

    print("全部完成")


if __name__ == "__main__":
    main()
